# ======================================================================
# Text encoder with attention-based pooling utilities.
# TODO: add token-level sentence wrapping so we avoid silent tokenizer truncation when texts exceed max_length.
# ======================================================================

import torch
import torch.nn.functional as F
import contextlib
from transformers import AutoModel, AutoTokenizer

from wordwield.core.device import device
from wordwield.core.norm   import Norm


class Encoder:
	
	def __init__(self, model_name=None):
		default_model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
		self.model_name    = model_name or default_model_name
		self.tokenizer     = AutoTokenizer.from_pretrained(self.model_name)
		self.model         = AutoModel.from_pretrained(self.model_name, attn_implementation='eager').to(device)
		self.model.eval()

	# ==========================================================================================
	# PRIVATE METHODS
	# ==========================================================================================

	# Centralized tokenizer to keep truncation/padding consistent
	# ----------------------------------------------------------------------
	def _tokenize(self, texts, padding):
		return self.tokenizer(
			texts,
			return_tensors = 'pt',
			padding        = padding,
			truncation     = True,
			max_length     = self.tokenizer.model_max_length
		)

	# Attention pooling over hidden states
	# ----------------------------------------------------------------------
	def _attention_pool(self, hidden_states, attentions):
		'''
		hidden_states: [S, D]
		attentions: list of [batch, heads, S, S] for each layer
		'''
		att = torch.stack(attentions)   # [L, B, H, S, S]
		att = att[:, 0]                 # take batch 0 → [L, H, S, S]
		att = att.mean(dim=1)           # average over heads → [L, S, S]
		att = att.mean(dim=0)           # average over layers → [S, S]

		weights = att[0]
		weights = F.softmax(weights, dim=0)

		ap_next = (weights.unsqueeze(1) * hidden_states).sum(dim=0)
		result = Norm.to_hypercube(ap_next)
		return result
	
	# ==========================================================================================
	# PUBLIC METHODS
	# ==========================================================================================

	# Eval mode
	# ----------------------------------------------------------------------
	def eval(self):
		return self.model.eval()

	# Encode a single text
	# ----------------------------------------------------------------------
	def encode(self, text, ap_prev=None, karma=1):
		amp_ctx = torch.cuda.amp.autocast if device.type == 'cuda' else contextlib.nullcontext
		with torch.inference_mode(), amp_ctx():
			tokens = self._tokenize(text, padding=False)
			tokens = {k: v.to(device) for k, v in tokens.items()}

			out    = self.model(**tokens, output_attentions=True)
			hidden = out.last_hidden_state.squeeze(0)
			attn   = out.attentions

			ap_next = self._attention_pool(hidden, attn)

			if ap_prev is not None:
				ap_prev = ap_prev.to(device)
				ap_next = ap_next + karma * ap_prev
				ap_next = Norm.to_hypercube(ap_next)

		return ap_next.to('cpu')

	# Encode a sequence of texts
	# ----------------------------------------------------------------------
	def encode_sequence(self, texts, ap_prev=None, karma=1):
		embeddings = []
		for text in texts:
			ap_next = self.encode(text, ap_prev=ap_prev, karma=karma)
			embeddings.append(ap_next)
		result = torch.stack(embeddings)
		return result

	# Test function to see if batch encode is semantically equal to single encode
	# ----------------------------------------------------------------------
	def test_encode_batch(self, texts, sample_size=20, batch_size=32):
		import random
		import torch.nn.functional as F

		# choose sample
		if len(texts) > sample_size : sample = random.sample(texts, sample_size)
		else                        : sample = texts

		print('\n=== encode() vs encode_batch_magic() consistency test ===')
		print(f'Comparing {len(sample)} texts...\n')

		# 1) magic batch encode (no padding → identical)
		ap_batch = self.encode_batch(sample)

		sims = []

		# 2) compare one-by-one
		for i, t in enumerate(sample):
			ap_single = self.encode(t)
			ap_b      = ap_batch[i]

			sim = F.cosine_similarity(
				ap_single.unsqueeze(0),
				ap_b.unsqueeze(0)
			).item()

			sims.append(sim)
			print(f'[{i:02d}] sim={sim:.6f} | text={t}')

		sims = torch.tensor(sims)

		print('\n=== Summary ===')
		print(f'Min similarity  : {sims.min().item():.6f}')
		print(f'Max similarity  : {sims.max().item():.6f}')
		print(f'Mean similarity : {sims.mean().item():.6f}')

		return sims

	# Encode a batch of texts without connecting them AP vector
	# ----------------------------------------------------------------------
	@torch.inference_mode()
	def encode_batch(self, texts, ap_prev_batch=None, karma=1, batch_size=32):
		amp_ctx = torch.cuda.amp.autocast if device.type == 'cuda' else contextlib.nullcontext
		with amp_ctx():
			# Tokenize
			tokens = self._tokenize(texts, padding=True)
			tokens = {k: v.to(device) for k, v in tokens.items()}

			out = self.model(**tokens, output_attentions=True)

			hidden = out.last_hidden_state      # [B, S, D]
			attns  = out.attentions             # tuple(L) of [B, H, S, S]
			mask   = tokens['attention_mask']   # [B, S]

			ap_list = []
			B = hidden.size(0)

			for b in range(B):
				seq_len  = mask[b].sum().item()  # ignore padding so outputs match encode()
				hidden_b = hidden[b, :seq_len]   # [S, D]

				# Build tuple of [H, S, S] tensors as encode() expects
				# Unsqueeze batch dim to match attention_pool()'s [B, H, S, S] expectation
				att_b   = tuple(layer[b, :, :seq_len, :seq_len].unsqueeze(0) for layer in attns)  # tuple(L), each [1, H, S, S]
				ap_next = self._attention_pool(hidden_b, att_b)

				# Optional recurrence
				if ap_prev_batch is not None:
					ap_prev = ap_prev_batch[b].to(device)
					ap_next = ap_next + karma * ap_prev
					ap_next = Norm.to_hypercube(ap_next)

				ap_list.append(ap_next.cpu())

		return torch.stack(ap_list)