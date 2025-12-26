# ======================================================================
# Text encoder with attention-based pooling utilities.
# TODO: add token-level sentence wrapping so we avoid silent tokenizer truncation when texts exceed max_length.
# TODO: add pooling choice: pooling='attention|mean|cls'
# ======================================================================

import os
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

		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
		self.model     = AutoModel.from_pretrained(self.model_name, attn_implementation = 'eager').to(device)
		self.dim       = self.model.config.hidden_size

		self.model.eval()

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

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

	# Get amp
	# ----------------------------------------------------------------------
	def _get_amp(self, with_attentions):
		amp_ctx = torch.cuda.amp.autocast if device.type == 'cuda' else contextlib.nullcontext
		amp     = amp_ctx if with_attentions else contextlib.nullcontext
		return amp
	
	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Pool hidden states into a single AP vector
	# ----------------------------------------------------------------------
	def attention_pool(self, hidden_states, attentions=None):
		'''
		hidden_states: [S, D]
		attentions:
			- None            → fast pooling (no attentions)
			- list of tensors → attention pooling (full mode)
		'''

		# ----------------------------------------------------------------------
		# FAST PATH: no attentions
		# ----------------------------------------------------------------------
		if attentions is None:
			# Simple mean pooling over sequence
			ap_next = hidden_states.mean(dim=0)
			return Norm.to_hypercube(ap_next)

		# ----------------------------------------------------------------------
		# FULL PATH: attention pooling
		# ----------------------------------------------------------------------
		att = torch.stack(attentions)   # [L, B, H, S, S]
		att = att[:, 0]                 # [L, H, S, S]
		att = att.mean(dim=1)           # [L, S, S]
		att = att.mean(dim=0)           # [S, S]

		weights = att[0]
		weights = F.softmax(weights, dim=0)

		ap_next = (weights.unsqueeze(1) * hidden_states).sum(dim=0)
		return Norm.to_hypercube(ap_next)

	# Eval mode
	# ----------------------------------------------------------------------
	def eval(self):
		return self.model.eval()

	# Encode a single text
	# ----------------------------------------------------------------------
	def encode(self, text, ap_prev=None, karma=1, with_attentions=True):
		amp = self._get_amp(with_attentions)

		with torch.inference_mode(), amp():
			tokens = self._tokenize(text, padding=False)
			tokens = {k: v.to(device) for k, v in tokens.items()}

			out     = self.model(**tokens, output_attentions=with_attentions)
			hidden  = out.last_hidden_state.squeeze(0)
			attn    = out.attentions if with_attentions else None
			ap_next = self.attention_pool(hidden, attn)

			if ap_prev is not None:
				ap_prev = ap_prev.to(device)
				ap_next = ap_next + karma * ap_prev
				ap_next = Norm.to_hypercube(ap_next)

		return ap_next.to('cpu')

	# Encode a sequence of texts (naive)
	# ----------------------------------------------------------------------
	def encode_sequence(self, texts, ap_prev=None, karma=1, with_attentions=True):
		embeddings = []
		prev       = ap_prev

		for text in texts:
			ap_next = self.encode(
				text,
				ap_prev         = prev,
				karma           = karma,
				with_attentions = with_attentions
			)
			embeddings.append(ap_next)
			prev = ap_next

		result = torch.stack(embeddings)
		return result
	
	# Encode a sequence of texts (as batch)
	# ----------------------------------------------------------------------
	def encode_sequence_batch(self, texts, ap_prev=None, karma=1, with_attentions=True):
		ap_static = self.encode_batch(
			texts,
			karma           = karma,
			with_attentions = with_attentions
		)

		ap_next = self.apply_batch_context(
			ap_static,
			ap_prev = ap_prev,
			karma   = karma
		)

		return ap_next

	# Encode a batch of texts (optionally with attentions)
	# ----------------------------------------------------------------------
	def encode_batch(self, texts, ap_prev_batch=None, karma=1, with_attentions=True):
		amp = self._get_amp(with_attentions)

		with torch.inference_mode(), amp():
			# Tokenize
			tokens = self._tokenize(texts, padding=True)
			tokens = {k: v.to(device) for k, v in tokens.items()}

			out = self.model(**tokens, output_attentions=with_attentions)

			hidden = out.last_hidden_state      # [B, S, D]
			attns  = out.attentions             # tuple(L) of [B, H, S, S] or None
			mask   = tokens['attention_mask']   # [B, S]

			ap_list = []
			B = hidden.size(0)

			for b in range(B):
				seq_len  = mask[b].sum().item()
				hidden_b = hidden[b, :seq_len]

				if with_attentions:
					# Build tuple of [1, H, S, S] tensors as attention_pool expects
					att_b = tuple(
						layer[b, :, :seq_len, :seq_len].unsqueeze(0)
						for layer in attns
					)
				else:
					att_b = None

				ap_next = self.attention_pool(hidden_b, att_b)

				# Optional recurrence (batch-wise)
				if ap_prev_batch is not None:
					ap_prev = ap_prev_batch[b].to(device)
					ap_next = ap_next + karma * ap_prev
					ap_next = Norm.to_hypercube(ap_next)

				ap_list.append(ap_next.cpu())

		return torch.stack(ap_list)

	# Apply left-to-right AP context over batch-encoded AP vectors
	# ----------------------------------------------------------------------
	def apply_batch_context(self, ap_static_batch, ap_prev=None, karma=1):
		'''
		Apply contextual recurrence over batch AP values.

		This is mathematically identical to encode_sequence(texts, ap_prev),
		assuming ap_static_batch[i] == encode(texts[i], prev_ap=None).
		'''

		n          = ap_static_batch.size(0)
		ap_dynamic = []

		prev = ap_prev

		for i in range(n):
			ap_next = ap_static_batch[i]

			if prev is not None:
				ap_next = ap_next + karma * prev
				ap_next = Norm.to_hypercube(ap_next)

			ap_dynamic.append(ap_next)
			prev = ap_next

		return torch.stack(ap_dynamic)
	
	# ======================================================================
	# TEST METHODS
	# ======================================================================

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
	
	# Test that encode_sequence == encode_batch + apply_batch_context
	# ----------------------------------------------------------------------
	def test_apply_batch_context(self, texts, ap_prev=None, karma=1, atol=1e-6):
		import torch
		import torch.nn.functional as F

		print('\n=== encode_sequence vs encode_batch + apply_batch_context ===')
		print(f'Texts: {len(texts)}')
		print(f'Initial ap_prev: {"yes" if ap_prev is not None else "no"}')
		print(f'Karma: {karma}\n')

		# 1) Reference: incremental encode
		ap_inc = self.encode_sequence(
			texts,
			ap_prev = ap_prev,
			karma   = karma
		)

		# 2) Factorized path: batch + context
		ap_static = self.encode_batch(
			texts,
			karma = karma
		)

		ap_ctx = self.apply_batch_context(
			ap_static,
			ap_prev = ap_prev,
			karma   = karma
		)

		assert ap_inc.shape == ap_ctx.shape

		# 3) Compare element-wise
		diffs = torch.norm(ap_inc - ap_ctx, dim=1)

		max_diff  = diffs.max().item()
		mean_diff = diffs.mean().item()

		print(f'Max L2 diff  : {max_diff:.8f}')
		print(f'Mean L2 diff : {mean_diff:.8f}')

		# cosine sanity (should be ~1)
		cos = F.cosine_similarity(ap_inc, ap_ctx)
		print(f'Min cosine   : {cos.min().item():.8f}')
		print(f'Mean cosine  : {cos.mean().item():.8f}')

		if not torch.allclose(ap_inc, ap_ctx, atol=atol):
			raise AssertionError(
				f'apply_batch_context mismatch: max_diff={max_diff}'
			)

		print('\n✓ apply_batch_context is EXACTLY equivalent to encode_sequence')
		return True

