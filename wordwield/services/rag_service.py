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
		step_top_k
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

		# res = yo.twinkle.Resonator(vectors)
		# res.step_top_k = step_top_k

		# res.add_facet('S', dim=0)
		# res.add_facet('D', dim=1)
		# res.facets['D'].input(query_vector)

		# idx = res.resonate(
		# 	query_vector,
		# 	max_steps = max_steps
		# )

		# step_ids = find_step_ids(lines)
		# idx = sorted(step_ids)
		# idx = res.test(step_ids, top_k=20)

		retriever = yo.retrievers.SentenceRetriever(texts, vectors, max_steps, step_top_k)

		return retriever.retrieve(query_vector)


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
					step_top_k    = top_k,
					max_steps     = max_steps
				)

				if lines:
					results[document.key] = lines

		return results

