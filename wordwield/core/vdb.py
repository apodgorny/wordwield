# ======================================================================
# Vector database wrapper for FAISS + encoding helpers.
# ======================================================================

import os

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('OMP_NUM_THREADS', '1')

import faiss
import numpy as np

from wordwield.core.encoder      import Encoder
from wordwield.core.norm         import Norm
from wordwield.core.sentencizers import PysbdSentencizer as Sentencizer


class Vdb:
	def __init__(self):
		self.encoder     = Encoder()
		self.max_length  = self.encoder.tokenizer.model_max_length
		self.dim         = self.encoder.model.config.hidden_size
		self.sentencizer = Sentencizer()
		self.indexes     = {}  # domain → FAISS index
		self.storage     = {}  # domain → {id: vector}
		faiss.omp_set_num_threads(1)

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Get (or create) FAISS index and storage for a domain
	# ----------------------------------------------------------------------
	def _get_domain_index(self, domain):
		if domain not in self.indexes:
			self.indexes[domain] = faiss.IndexIDMap(
				faiss.IndexFlatIP(self.dim)
			)
			self.storage[domain] = {}  # id → vector
		return self.indexes[domain], self.storage[domain]

	# Search within ID range
	# ----------------------------------------------------------------------
	def _search_range(self, index, vec, k, id_range):
		n     = max(k * 4, 50)
		pairs = []

		while True:
			scores, ids = index.search(vec.reshape(1, -1), n)
			n          *= 2

			pairs = [
				(i, s)
				for (i, s) in zip(ids[0], scores[0])
				if id_range.start <= i <= id_range.stop - 1
			]

			if len(pairs) >= k:
				break
			if n > index.ntotal:
				break

		pairs.sort(key=lambda item: item[1], reverse=True)
		result = [i for (i, s) in pairs[:k]]
		return result

	# Search within entire domain
	# ----------------------------------------------------------------------
	def _search_global(self, index, vec, k):
		scores, ids = index.search(vec.reshape(1, -1), k)
		result = [int(x) for x in ids[0] if x >= 0]
		return result

	# Encode query vector with optional initial AP
	# ----------------------------------------------------------------------
	def _encode_query_vector(self, text, ap_prev, karma):
		sents    = self.sentencizer.to_sentences(text)
		is_valid = False
		vec      = None
		ap_next   = ap_prev

		if sents:
			seq      = self.encoder.encode_sequence(sents, ap_prev=ap_prev, karma=karma)
			ap_next   = seq[-1].cpu()
			is_valid = True
			vec      = Norm.to_sphere(ap_next).cpu().numpy().astype('float32')

		return vec, ap_next, is_valid

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Add vector with explicit ID
	# ----------------------------------------------------------------------
	def add(self, domain, id, text):
		index, storage = self._get_domain_index(domain)

		id  = int(id)
		vec = self.encoder.encode(text)
		vec = Norm.to_sphere(vec).cpu().numpy().astype('float32')

		index.add_with_ids(
			vec.reshape(1, -1),
			np.array([id], dtype='int64')
		)

		storage[id] = vec
		return id

	# Add vector batch with explicit IDs
	# ----------------------------------------------------------------------
	def add_many(self, domain, ids, texts=None, ap_prev=None, vectors=None):
		index, storage = self._get_domain_index(domain)
		ap_next        = ap_prev

		if vectors is None:
			ap_seq  = self.encoder.encode_sequence(texts, ap_prev=ap_prev)
			vecs    = Norm.to_sphere(ap_seq).cpu().numpy().astype('float32')
			ap_next = ap_seq[-1].cpu()
		else:
			vecs = np.array(vectors, dtype='float32')

		ids = np.array(ids, dtype='int64')
		index.add_with_ids(vecs, ids)

		for i, vec in zip(ids, vecs):
			storage[int(i)] = vec

		return ap_next

	# Remove vector by ID
	# ----------------------------------------------------------------------
	def remove(self, domain, id):
		index, storage = self._get_domain_index(domain)

		id = int(id)
		index.remove_ids(np.array([id], dtype='int64'))
		storage.pop(id, None)
		return None

	# Query vectors by text
	# ----------------------------------------------------------------------
	def query(self, domain, text, k=5, id_range=None, ap_prev=None, karma=0.5):
		index, _             = self._get_domain_index(domain)
		vec, ap_next, valid = self._encode_query_vector(text, ap_prev, karma)
		found_ids            = []

		if valid:
			if id_range is None : found_ids = self._search_global(index, vec, k)
			else                : found_ids = self._search_range(index, vec, k, id_range)

		return found_ids, ap_next

	# Number of vectors in a domain
	# ----------------------------------------------------------------------
	def domain_size(self, domain):
		index, _ = self._get_domain_index(domain)
		return index.ntotal
