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

	# Alias for to_sphere
	# ----------------------------------------------------------------------
	@staticmethod
	def s(v):
		result = Norm.to_sphere(v)
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

	#  Alias for to_hypercube
	# ----------------------------------------------------------------------
	@staticmethod
	def h(v):
		result = Norm.to_hypercube(v)
		return result
