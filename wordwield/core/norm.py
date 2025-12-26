# ======================================================================
# Vector normalization helpers.
# ======================================================================

import torch


epsilon = 1e-8


class Norm:
	# Project to unit sphere
	# ----------------------------------------------------------------------
	@staticmethod
	def to_sphere(v):
		result = v
		if v.dim() == 1:
			result = v / (v.norm() + epsilon)
		else:
			result = v / (v.norm(dim=1, keepdim=True) + epsilon)
		return result


	# Project to hypercube
	# ----------------------------------------------------------------------
	@staticmethod
	def to_hypercube(v):
		if v.dim() == 1:
			m = v.abs().max()
			return v / (m + epsilon)
		m = v.abs().max(dim=1, keepdim=True).values
		return v / (m + epsilon)
	
	# Pac-Man Normalization
	# ----------------------------------------------------------------------
	def pacman(v, turns=None):
		turns = turns if turns is not None else torch.zeros_like(v, dtype=torch.int64)
		assert v.shape == turns.shape

		whole     = torch.floor(v).to(dtype=turns.dtype)   # 1. целая часть по каждой ности
		v_norm    = v - whole                              # 2. остаток — локальная фаза
		angles    = torch.acos(v_norm)                     # 3. угол из косинуса

		new_turns = turns + whole

		return v_norm, angles, new_turns

	# Aliases
	# ----------------------------------------------------------------------
	@staticmethod
	def s(v): return Norm.to_sphere(v)

	@staticmethod
	def h(v): return Norm.to_hypercube(v)

	@staticmethod
	def p(v, t): return Norm.pacman(v, t)
