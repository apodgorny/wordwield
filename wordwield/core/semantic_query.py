import math
import torch as T



class SemanticQuery:
	# ----------------------------------------------------------------------
	def __init__(self, vectors):
		self.vectors = vectors
		self.kernel  = self._build_affinity_kernel()
		self.S       = len(vectors)

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Create affinity kernel [S, S] of cosine similarities
	# ----------------------------------------------------------------------
	def _build_affinity_kernel(self):
		V = self.vectors # [S, D], float32

		norms = T.linalg.norm(V, dim=1, keepdim=True)
		safe_norms = T.where(
			norms > 1e-6,
			norms,
			T.ones_like(norms)
		)

		V_phase = V / safe_norms              # нормализуем направление
		K = V_phase @ V_phase.T               # чистая фазовая интерференция

		return K.to(dtype=T.float32)

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Seed vector idx -> relevance-sorted list of item idx
	# ----------------------------------------------------------------------
	def excite(self, seed_ids):
		return T.argsort(
			T.mean(self.kernel[seed_ids], dim=0),
			descending = True
		)
	
	def condense(self, q0, k=8, karma=0.9, eps=0.001, max_steps=16):

		def get_seeds(q):
			qn = q / (T.linalg.norm(q) + 1e-6)
			Vn = self.vectors / (T.linalg.norm(self.vectors, dim=1, keepdim=True) + 1e-6)
			return T.argsort(Vn @ qn, descending=True)[:k]

		def step(seed_ids, q):
			order = self.excite(seed_ids)                 # semantic echo
			top   = order[:k]                             # structure carriers
			a_t   = T.mean(self.vectors[top], dim=0)      # structural anchor
			q_t   = karma * q0 + (1 - karma) * a_t         # intention + structure
			return q_t, top

		def condition(q_prev, q_cur, step_idx):
			if q_prev is None:
				return False
			if T.linalg.norm(q_cur - q_prev) < eps:
				return True                               # saturation
			if step_idx >= max_steps:
				return True                               # safety stop
			return False

		q_prev = None
		q      = q0
		top    = None

		for i in range(max_steps):
			print('Step', i)
			seed_ids     = get_seeds(q)
			q_next, top  = step(seed_ids, q)
			print('Seeds', seed_ids.tolist())
			# print('q', q_next)

			if condition(q_prev, q_next, i):
				break

			q_prev = q
			q      = q_next

		return q, top
	
	def skeletonize(self):
		V = self.vectors
		deltas = 1 - T.cosine_similarity(V[1:], V[:-1])
		return T.argsort(deltas, descending=True)

	def select(self, query_vector, k=8, alpha=0.5):
		_, cond_top = self.condense(query_vector, k=k)
		skel_top   = self.skeletonize()[:k]

		cond_set = set(cond_top.tolist())
		skel_set = set(skel_top.tolist())

		combined = cond_set | skel_set
		return sorted(combined)
