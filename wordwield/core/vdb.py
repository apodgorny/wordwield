# ======================================================================
# Vector database wrapper for FAISS + encoding helpers.
# ======================================================================

import os

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('OMP_NUM_THREADS', '1')

import faiss
import numpy as np

from wordwield.core.norm import Norm
from wordwield.core.vid  import Vid


class Vdb:
	def __init__(self, dim):
		self.dim         = dim # encoder.model.config.hidden_size
		self.indexes     = {}  # domain → FAISS index
		faiss.omp_set_num_threads(1)

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Get (or create) FAISS index for a domain
	# ----------------------------------------------------------------------
	def _get_domain_index(self, domain):
		if domain not in self.indexes:
			self.indexes[domain] = faiss.IndexIDMap(
				faiss.IndexFlatIP(self.dim)
			)
		return self.indexes[domain]

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Add vector batch with explicit IDs (Vid ints)
	# ----------------------------------------------------------------------
	def add(self, domain, v_ids, vectors):
		assert len(v_ids) == len(vectors)

		faiss_index = self._get_domain_index(domain)
		faiss_vecs  = Norm.to_sphere(vectors).cpu().numpy().astype('float32')
		faiss_index.add_with_ids(faiss_vecs, np.array(v_ids, dtype='int64'))

	# Remove vectors by explicit IDs
	# ----------------------------------------------------------------------
	def remove_ids(self, domain, v_ids):
		if v_ids:
			faiss_index = self._get_domain_index(domain)
			selector = faiss.IDSelectorArray(np.array(v_ids, dtype='int64'))
			faiss_index.remove_ids(selector)

	# Query vectors by vector, optionally restricted to doc_ids
	# ----------------------------------------------------------------------
	def query(self, domain, query_vector, k=5, doc_ids=None):
		faiss_index  = self._get_domain_index(domain)
		query_vector = Norm.to_sphere(query_vector).reshape(1, -1)

		n = max(k * 8, 64)
		scores, ids = faiss_index.search(query_vector, n)

		allowed_docs = set(doc_ids) if doc_ids is not None else None
		result       = []
		seen         = set()

		for faiss_id, score in zip(ids[0], scores[0]):
			if faiss_id >= 0:
				ok = True

				if allowed_docs is not None:
					ok = Vid(hash=faiss_id).doc_id in allowed_docs

				if ok and faiss_id not in seen:
					result.append(faiss_id)
					seen.add(faiss_id)

		return result

	# Number of vectors in a domain
	# ----------------------------------------------------------------------
	def domain_size(self, domain):
		return self._get_domain_index(domain).ntotal
