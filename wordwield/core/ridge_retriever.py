import torch as T
import torch.nn.functional as F


class RidgeRetriever:
	'''
	Ridge-based retrieval with 2-stage attention.

	ap_dynamic: entry / local meaning
	V_att     : structure / continuity
	'''

	def __init__(self, vectors, vectors_att):
		assert vectors.shape == vectors_att.shape

		self.vectors     = vectors
		self.vectors_att = vectors_att
		self.seq_len     = vectors.size(0)

	# ----------------------------------------------------------------------

	def _median_similarity(self):
		neighbour_sims = T.tensor([
			self._cos_v(i, i + 1)
			for i in range(self.seq_len - 1)
		])
		return neighbour_sims.median().item()

	def _find_ridge(self, seed, ridge_threshold ):
		l,r = seed, seed
		while l > 0                and self._cos_v(l - 1, l) >= ridge_threshold: l -= 1
		while r < self.seq_len - 1 and self._cos_v(r, r + 1) >= ridge_threshold: r += 1
		return list(range(l, r + 1))
	
	def _cos_v(self, n1, n2):
		a = self.vectors_att[n1]
		b = self.vectors_att[n2]
		return self._cos(a, b).item()

	def _cos(self, a, b):
		if len(a.shape) < 2: a = a.unsqueeze(0)
		if len(b.shape) < 2: b = b.unsqueeze(0)
		return F.cosine_similarity(a, b)

	# Produce top
	# ----------------------------------------------------------------------
	def get_seeds(self, ap_query, top_k):
		relevance = self._cos(ap_query, self.vectors)
		seeds = T.topk(relevance, k=top_k).indices.tolist()
		return seeds
	
	def expand_ridges(self, seeds, ridge_threshold):
		visited = set()
		ridges  = []

		for seed in seeds:
			if seed not in visited:
				ridge = self._find_ridge(seed, ridge_threshold)
				visited.update(ridge)
				ridges.append(ridge)

		return ridges

	# Ridge detection
	# ----------------------------------------------------------------------
	def retrieve(
		self,
		ap_query,
		*,
		top_k           = 5,
		ridge_threshold = None
	):
		top_k           = min(top_k, self.seq_len)
		seeds           = self.get_seeds(ap_query, top_k)
		ridge_threshold = ridge_threshold or self._median_similarity()
			
		return self.expand_ridges(seeds, ridge_threshold)