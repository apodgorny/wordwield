# ======================================================================
# SentenceDecoder — AP → Text Generator (v0.3)
# Freezes GPT-2 embeddings + lower transformer blocks,
# trains upper blocks + LM head + AP projection layer.
# ======================================================================

import time

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import GPT2LMHeadModel, GPT2TokenizerFast
from tqdm import tqdm

from wordwield.core.device import device
from wordwield.core.norm   import Norm
from wordwield.core.kaggle import Kaggle


# ======================================================================
# SentenceDataset
# ======================================================================

class SentenceDataset(Dataset):
	def __init__(self, path):
		state = torch.load(path, map_location='cpu')

		self.aps   = state['aps']			  # list[tensor]	   shape [384]
		self.ids   = state['input_ids']		  # list[tensor]	   shape [max_len]
		self.masks = state['attention_mask']  # list[tensor]	   shape [max_len]

	def __len__(self):
		return len(self.aps)

	def __getitem__(self, idx):
		return (
			self.aps[idx],	 # AP vector
			self.ids[idx],	 # token ids
			self.masks[idx]	 # mask
		)


# ======================================================================
# SentenceDecoder
# ======================================================================

class SentenceDecoder(nn.Module):
	def __init__(self, ap_dim=384, model_name='gpt2', freeze_lower_k=10):
		super().__init__()

		self.gpt	   = GPT2LMHeadModel.from_pretrained(model_name).to(device)
		self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)

		# GPT-2 has no pad token → set pad = eos
		if self.tokenizer.pad_token is None:
			self.tokenizer.pad_token     = self.tokenizer.eos_token
			self.gpt.config.pad_token_id = self.tokenizer.eos_token_id


		hidden = self.gpt.config.hidden_size
		self.proj = nn.Linear(ap_dim, hidden).to(device)


		# ======================================================================
		# FREEZE STRATEGY
		# ======================================================================

		# Freeze embeddings: token + positional
		self.gpt.transformer.wte.requires_grad_(False)
		self.gpt.transformer.wpe.requires_grad_(False)

		# Freeze lower K decoder blocks
		# Example: GPT-2 small has 12 layers → freeze 10 → train last 2
		for i, block in enumerate(self.gpt.transformer.h):
			if i < freeze_lower_k:
				for p in block.parameters():
					p.requires_grad = False

		# Keep upper blocks trainable (they remain unfrozen)
		# Train LM head

		for p in self.gpt.lm_head.parameters():
			p.requires_grad = True

		# Projection layer always trainable
		for p in self.proj.parameters():
			p.requires_grad = True

		self.state = {}

	# ======================================================================
	# LOAD / SAVE
	# ======================================================================

	def save(self, path):
		torch.save(self.state_dict(), path)
		print(f'Saved trained SentenceDecoder weights → {path}')
		return path

	def load(self):
		kaggle_dataset_id   = 'alexanderpodgorny/sentence-decoder'
		kaggle_dataset_file = 'sentence_decoder.pt'

		state = Kaggle().load(kaggle_dataset_id, kaggle_dataset_file)
		self.load_state_dict(state)
		print(f'Loaded SentenceDecoder weights ← {path}')
		return True

	# ======================================================================
	# INFERENCE
	# ======================================================================

	def decode(self, ap_vector, max_len=40, temperature=0.9, top_p=0.95):
		ap = Norm.to_hypercube(ap_vector).to(device)
		prefix = self.proj(ap).unsqueeze(0).unsqueeze(1)

		output = self.gpt.generate(
			inputs_embeds  = prefix,
			max_length     = max_len,
			do_sample      = True,
			temperature    = temperature,
			top_p          = top_p,
			pad_token_id   = self.tokenizer.eos_token_id,
			attention_mask = torch.ones((1, 1), device=prefix.device)  # Don't need for inference, setting to avoid warning
		)

		return self.tokenizer.decode(output[0], skip_special_tokens=True)

	# ======================================================================
	# TRAINING LOOP
	# ======================================================================

	def train_model(
		self,
		path,
		batch_size  = 32,   # увеличили для максимальной скорости
		lr          = 3e-5,
		epochs      = 1,
		accum_steps = 1,    # убрали аккумуляцию — быстрее
		max_len     = 64,
		save_dir    = '/kaggle/working'
	):
		# ----------------------------------------------------------------------
		# Load dataset (AP + GPT-2 tokens)
		# ----------------------------------------------------------------------
		dataset = SentenceDataset(path)
		loader  = DataLoader(
			dataset,
			batch_size  = batch_size,
			shuffle     = True,
			num_workers = 2,          # Kaggle loves 2
			pin_memory  = True
		)
	
		# ----------------------------------------------------------------------
		# Optimizer + FP16 scaler
		# ----------------------------------------------------------------------
		params  = filter(lambda p: p.requires_grad, self.parameters())
		optim   = torch.optim.AdamW(params, lr=lr)
		scaler  = torch.cuda.amp.GradScaler() if device.type == 'cuda' else None
		amp_ctx = torch.amp.autocast          if device.type == 'cuda' else contextlib.nullcontext
	
		self.train()
	
		print(f'\n🚀 Training started on {device}\n')
	
		for epoch in range(epochs):
			start_time    = time.time()
			token_counter = 0
	
			loop = tqdm(loader, desc=f'Epoch {epoch+1}/{epochs}')
	
			for ap, ids, mask in loop:
				ap   = ap.to(device)
				ids  = ids.to(device)
				mask = mask.to(device)
	
				# ----------------------------------------------------------------------
				# Build prefix from AP → GPT-2 hidden
				# ----------------------------------------------------------------------
				prefix = self.proj(ap).unsqueeze(1)
	
				# token embeddings
				inputs_embeds = self.gpt.transformer.wte(ids)
				inputs_embeds[:, 0, :] = prefix[:, 0, :]
	
				with amp_ctx(device_type='cuda', dtype=torch.float16) if device.type == 'cuda' else amp_ctx():
					outputs = self.gpt(
						inputs_embeds  = inputs_embeds,
						attention_mask = mask,
						labels         = ids
					)
					loss = outputs.loss
	
				# FP16 backward
				if scaler:
					scaler.scale(loss).backward()
					scaler.step(optim)
					scaler.update()
				else:
					loss.backward()
					optim.step()
	
				optim.zero_grad()
	
				# ---------------------------------------------------------------------- speed tracking ----
				token_counter += ids.numel()
				tokens_per_sec = token_counter / (time.time() - start_time)
	
				loop.set_postfix({
					'loss'  : f'{loss.item():.4f}',
					'tok/s' : f'{tokens_per_sec:.0f}'
				})
	
			# ----------------------------------------------------------------------
			# SAVE CHECKPOINT AFTER EACH EPOCH
			# ----------------------------------------------------------------------
			save_path = f'{save_dir}/sentence_decoder_epoch{epoch+1}.pt'
			torch.save(self.state_dict(), save_path)
			print(f'\n💾 Epoch {epoch+1} saved → {save_path}\n')
	
		print('\n✨ Training complete.\n')
