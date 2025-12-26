# ======================================================================
# Semantic search service built on EncoderService ridge scanning helpers.
# ======================================================================

import numpy as np
import torch as T
import torch.nn.functional as F

from wordwield.core.base.service import Service
from wordwield.core.norm         import Norm
from wordwield.libs.viz          import Viz
from wordwield.core.device       import device
from wordwield.core.ridge_retriever import RidgeRetriever


class SemanticSearchService(Service):

	# Initialize encoder and cached vectors
	# ----------------------------------------------------------------------
	def initialize(self):
		self.encoder = self.ww.services.EncoderService
		self.vectors     = None
		self.vectors_att = None
		self.ridges      = None
		self.texts       = None
		self.seq_len     = None

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Apply query-less self-attention (vectors [S, D] -> vectors_att [S, D])
	# ----------------------------------------------------------------------
	def _self_attention(self, vectors, eps=1e-8):
		S, D = vectors.shape
		A = (vectors.unsqueeze(1) + vectors.unsqueeze(0)) / 2   # [S, S, D] - attention kernel
		A = (vectors @ vectors.T) / D
		# norm = T.nn.functional.normalize(vectors, dim=1)
		# A = norm @ norm.T
		W = T.softmax(A, dim=1)                                 # normalize rows
		vectors_att = W @ vectors                               # [S, D] - attended vectors
		return Norm.to_hypercube(vectors_att)

	# Compute median similarity between consecutive vectors
	# ----------------------------------------------------------------------
	def _median_similarity(self):
		neighbour_sims = T.tensor([
			self._cos_v(i, i + 1)
			for i in range(self.seq_len - 1)
		])
		# F.cosine_similarity(V, V.roll(1, 0)) ??
		return neighbour_sims.median().item()

	# Expand a ridge from a seed index based on similarity threshold
	# ----------------------------------------------------------------------
	def _find_ridge(self, seed, ridge_threshold):
		l, r = seed, seed
		while l > 0                and self._cos_v(l - 1, l) >= ridge_threshold: l -= 1
		while r < self.seq_len - 1 and self._cos_v(r, r + 1) >= ridge_threshold: r += 1
		return list(range(l, r + 1))

	# Compute cosine similarity between two attended vectors
	# ----------------------------------------------------------------------
	def _cos_v(self, n1, n2):
		a = self.vectors_att[n1]
		b = self.vectors_att[n2]
		return self._cos(a, b).item()

	# Compute cosine similarity between tensors
	# ----------------------------------------------------------------------
	def _cos(self, a, b):
		if len(a.shape) < 2: a = a.unsqueeze(0)
		if len(b.shape) < 2: b = b.unsqueeze(0)
		return F.cosine_similarity(a, b)

	# Retrieve seed indices most similar to the query
	# ----------------------------------------------------------------------
	def _get_seeds(self, ap_query, top_k):
		relevance = self._cos(ap_query, self.vectors)
		seeds = T.topk(relevance, k=top_k).indices.tolist()
		return seeds

	# Expand ridges from seeds while avoiding overlap
	# ----------------------------------------------------------------------
	def _expand_ridges(self, seeds, ridge_threshold):
		visited = set()
		ridges  = []

		for seed in seeds:
			if seed not in visited:
				ridge = self._find_ridge(seed, ridge_threshold)
				visited.update(ridge)
				ridges.append(ridge)

		return ridges

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform ridge detection on a query over scanned texts
	# ----------------------------------------------------------------------
	def search(self, query, top_k=5, ridge_threshold=None):
		if self.vectors is None or self.vectors_att is None:
			print('Warning: scan(texts) must be called prior to search(query)')
			return None

		print('Querying ...', end=' ', flush=True)
		ap_query        = self.encoder.encode(query)
		top_k           = min(top_k, self.seq_len)
		seeds           = self._get_seeds(ap_query, top_k)
		ridge_threshold = ridge_threshold or self._median_similarity()
		self.ridges     = self._expand_ridges(seeds, ridge_threshold)
		print('Done')

		return self

	# Scan texts to build vector and attention caches
	# ----------------------------------------------------------------------
	def scan(self, texts, ap_prev=None, karma=1, with_attentions=False):
		if texts:
			self.seq_len = len(texts)
			self.texts   = texts
			print('Scanning ...', end=' ', flush=True)
			self.vectors = self.encoder.encode_sequence_batch(
				texts,
				ap_prev         = ap_prev,
				karma           = karma,
				with_attentions = with_attentions
			)
			self.vectors_att = self._self_attention(self.vectors)
			print('Done')
		return self
	
	# Get ridge text
	# ----------------------------------------------------------------------
	def text(self):
		if self.ridges is None:
			print('Warning: scan(texts).search(query) must be called prior to text()')
			return None
		
		return [[self.texts[idx] for idx in ridge] for ridge in self.ridges]
	
	# Display ridges
	# ----------------------------------------------------------------------
	def disp(self, disp_idx=False):
		if disp_idx:
			print('Ridges:', self.ridges)
		
		for texts in self.text():
			print()
			print('\n'.join(texts))
		print()


'''
# Roll does [v1, v2, v3] -> [v3, v1, v2].
# После этого F.cosine_similarity(V, V.roll(1, 0)) вычисляет [cos(v2,v1), cos(v3,v2)].

shape_corr = F.cosine_similarity(V, V.roll(1, 0))  # соседняя схожесть
shape_corr = F.cosine_similarity(V[:-1], V[1:])

2. Как из плато делается attention mask

Берём бинарную маску ridge_mask, где:

ridge_mask[i] = 1  если shape_corr[i] > threshold
ridge_mask[i] = 0  иначе


Теперь нужно превратить её в матрицу [S, S], которая говорит,
какие токены/предложения должны "видеть" друг друга внутри плато.


def _build_affinity_kernel(self):
		# V — hypercube vectors, float32
		V = np.array(self.vectors)
		norms = np.linalg.norm(V, axis=1, keepdims=True)
		safe_norms = np.where(norms > 1e-6, norms, 1.0)

		V_phase = V / safe_norms            # нормализуем направление
		K = V_phase @ V_phase.T             # чистая фазовая интерференция

		return K.astype('float32')


'''

