# ======================================================================
# Rag service coordinating semantic DB and vector DB.
# ======================================================================

import torch

from wordwield.core.base.service          import Service
from wordwield.core.db.semantic_domain    import SemanticDomain
from wordwield.core.db.semantic_document  import SemanticDocument
from wordwield.core.db.semantic_atom      import vector_deserialize
from wordwield.core.vdb                   import Vdb
from wordwield.core.sid                   import Sid
from wordwield.core.sentencizers          import PysbdSentencizer as Sentencizer
from wordwield.libs.yo                    import yo


def make_halt_sentence_stability(
	top_k,
	facet_name = 'f_sentence_out',
	patience   = 1
):
	"""
	Halt when top_k sentence indices stop changing.

	patience = how many consecutive identical steps are required
	"""

	last_set     = None
	stable_steps = 0

	def halt(**facets):
		nonlocal last_set, stable_steps

		kernel = facets.get(facet_name)
		if kernel is None:
			return False

		# Take top-k indices
		idx = np.argsort(np.abs(kernel))[-top_k:]
		curr_set = set(idx.tolist())

		if curr_set == last_set:
			stable_steps += 1
		else:
			stable_steps = 0
			last_set     = curr_set

		return stable_steps >= patience

	return halt



class RagService(Service):

	# To initialize vector database and hydrate it from persistent atoms.
	# ------------------------------------------------------------------
	def initialize(self):
		self.encoder     = self.ww.encoder
		self.sentencizer = Sentencizer()
		self.vdb         = Vdb(self.ww.encoder.dim)
		self._hydrate()

	# ==================================================================
	# PRIVATE METHODS
	# ==================================================================

	# Restore persistent semantic atoms into vector DB.
	# Remove all temporary domains from database.
	# ------------------------------------------------------------------
	def _hydrate(self):
		try:
			# 1. Drop all temporary domains (DB only)
			# ------------------------------------------------------------------
			for domain in SemanticDomain.get_all(temporary=True):
				SemanticDomain.unset(domain.id)

			# 2. Load persistent domains into VDB
			# ------------------------------------------------------------------
			for domain in SemanticDomain.get_all(temporary=False):

				vector_ids    = []
				vector_values = []

				for document in domain.get_documents():
					for atom in document.atoms:
						vector = vector_deserialize(atom.vector)
						if vector is not None:
							vector_ids.append(atom.id)
							vector_values.append(vector)
						else:
							raise ValueError('Vector deserialization failed')

				if vector_ids:
					vectors = torch.stack(vector_values)
					self.vdb.add(
						domain_id     = domain.id,
						vector_ids    = vector_ids,
						vector_values = vectors
					)
			self.ww.db.commit()

		except Exception:
			self.ww.db.rollback()
			raise

	# Split full document text into atom texts and vectors.
	# ------------------------------------------------------------------
	def _vectorize(self, text: str):
		texts   = self.sentencizer.to_sentences(text)
		vectors = self.encoder.encode_sequence(texts)
		return texts, vectors

	# ==================================================================
	# PUBLIC METHODS
	# ==================================================================

	# Create or ensure domain exists.
	# ------------------------------------------------------------------
	def set_domain(self, key: str, *, meta: str | None = None, temporary: bool = False) -> int:
		try:
			domain_id = SemanticDomain.set(
				key       = key,
				meta      = meta,
				temporary = temporary
			)
			self.ww.db.commit()
			return domain_id

		except Exception:
			self.ww.db.rollback()
			raise

	# Remove domain and all its documents and vectors.
	# ------------------------------------------------------------------
	def unset_domain(self, id_or_key: int | str) -> bool:
		try:
			removed = False
			domain  = SemanticDomain.get(id_or_key)

			if domain is not None:
				if SemanticDomain.unset(domain.id):
					self.vdb.remove(domain.id)
					removed = True

			self.ww.db.commit()
			return removed

		except Exception:
			self.ww.db.rollback()
			raise

	# Create or update document and fully reindex its atoms from full text.
	# Strategy: remove and re-insert (DB), range-remove (VDB).
	# ------------------------------------------------------------------
	def set_document(
		self,
		domain_id    : int | str,
		*,
		document_key : str,
		text         : str,
		mtime        : int,
		meta         : str | None = None
	) -> int:
		try:
			texts, vectors = self._vectorize(text)
			
			document_id = SemanticDocument.set(
				domain_id = domain_id,
				key       = document_key,
				mtime     = mtime,
				meta      = meta
			)

			document   = SemanticDocument.get(domain_id, document_id)
			vector_ids = document.set_atoms(texts, vectors)

			if vector_ids:
				vector_values = torch.stack(list(vectors)) if isinstance(vectors, list) else vectors

				self.vdb.add(
					domain_id     = domain_id,
					vector_ids    = vector_ids,
					vector_values = vector_values
				)

			self.ww.db.commit()
			return document_id

		except Exception:
			self.ww.db.rollback()
			raise

	# Remove document and all its atoms (DB + VDB)
	# ------------------------------------------------------------------
	def unset_document(self, domain_id: int, document_id: int) -> bool:
		try:
			removed  = False
			document = SemanticDocument.get(domain_id, document_id)

			if document is not None:
				self.vdb.remove(
					domain_id   = domain_id,
					document_id = document_id
				)
				SemanticDocument.unset(domain_id, document_id)
				removed = True

			self.ww.db.commit()
			return removed

		except Exception:
			self.ww.db.rollback()
			raise

	# List documents in domain
	# ------------------------------------------------------------------
	def get_documents(self, domain_id):
		domain = SemanticDomain.get(domain_id)
		if domain is not None:
			return domain.get_documents()

	def search_document(
		self,
		document,
		query_vector,
		max_steps,
		top_k
	):

		vectors   = []
		texts     = []
		atom_ids  = []

		for atom in document.atoms:
			vector = vector_deserialize(atom.vector)
			if vector is not None:
				vectors.append(vector)
				texts.append(atom.text)
				atom_ids.append(atom.id)

		if not vectors:
			return []

		vectors = yo.to_numpy(torch.stack(vectors))

		# --------------------------------------------------------------
		# Build SentenceRetriever from YAML via Twinkle
		# --------------------------------------------------------------

		twinkler = yo.twinkle.Twinkler.assemble(
			config   = yo.twinkle.apps.sentence_retriever,
			document = vectors,
			query    = query_vector,
			affinity = yo.kernels.Affinity(vectors)
		)

		mask = twinkler.twinkle(
			max_tics = max_steps,
			top_k    = top_k
		)

		# # idx сейчас — это НЕ indices, а history / output
		# # предполагаем, что sentence_out — последний mask
		# mask = twinkler.facets['f_sentence_out'].output()

		idx = self._score(
			mask         = mask,
			vectors      = vectors,
			query_vector = query_vector,
			top_k        = top_k
		)

		lines = [(i, texts[i]) for i in sorted(idx)]
		return lines


	# Search
	# ------------------------------------------------------------------
	def search(self, domain_id, query, top_k, max_steps):
		domain  = SemanticDomain.get(domain_id)
		results = {}

		if domain:
			query_vector = self.encoder.encode(query)
			for document in domain.get_documents():
				lines = self.search_document(
					document      = document,
					query_vector  = yo.to_numpy(query_vector),
					max_steps     = max_steps,
					top_k         = top_k
				)

				if lines:
					results[document.key] = lines

		return results


	def _score(
		self,
		mask,
		vectors,
		query_vector,
		top_k,
		threshold = 0.85,
		min_candidates = 8
	):
		import numpy as np

		# Phase 1: structural filtering
		candidates = [i for i, v in enumerate(mask) if v >= threshold]

		if len(candidates) < min_candidates:
			candidates = sorted(
				range(len(mask)),
				key=lambda i: mask[i],
				reverse=True
			)[:max(top_k * 3, min_candidates)]

		# Phase 2: semantic alignment
		q = query_vector / (np.linalg.norm(query_vector) + 1e-9)

		scored = []
		for i in candidates:
			v = vectors[i]
			v = v / (np.linalg.norm(v) + 1e-9)
			score = float((q * v).sum())
			scored.append((i, score))

		scored.sort(key=lambda x: x[1], reverse=True)
		return [i for i, _ in scored[:top_k]]
