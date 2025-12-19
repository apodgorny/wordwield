# ======================================================================
# RAG orchestration: DB CRUD, chunking, and FAISS sync.
# ======================================================================

import numpy as np

from tqdm                       import tqdm

from wordwield.core.base.service import Service
from wordwield.core.db           import RagDocument, RagDocumentChunk
from wordwield.core.norm         import Norm
from wordwield.core.sentencizers import PysbdSentencizer as Sentencizer
from wordwield.core.vdb          import Vdb
from wordwield.libs.viz          import Viz


class RagService(Service):

	def initialize(self):
		self.vdb         = Vdb()
		self.sentencizer = Sentencizer()
		self.reranker    = self.ww.services.RerankService

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Resolve document IDs for a domain and optional keys
	# ----------------------------------------------------------------------
	def _get_ids(self, domain, keys=None):
		record_ids = []
		if keys is None:
			record_rows = RagDocument.get_by_domain(domain)
			record_ids  = [r.id for r in record_rows]
		else:
			record_ids  = RagDocument.get_ids_by_keys(domain, keys)
		return record_ids
	
	def _print_scores(self, texts, bayes_scores, li_scores, effective):
		print('––– Bayes > 0 chunks –––')

		for text, b, l, e in zip(texts, bayes_scores, li_scores, effective):
				print(f'[bayes={b:.6f}, li={l:.6f}, effective={e:.6f}]')
				print(text.strip())
				print('––––––––––––––––––')

	
	# Detect ridges
	# ----------------------------------------------------------------------
	def _get_ridges(self, query, texts, ap_prev=None, karma=0.5):
		ridges = []

		if texts:
			# --------------------------------------------------
			# 1. Raw signals
			# --------------------------------------------------
			bayes_scores = self.reranker.rerank(
				None,
				texts,
				self.reranker.BAYES
			)

			li_scores = self.reranker.rerank(
				query,
				texts,
				self.reranker.LATE_INTERACTION
			)

			bayes = np.asarray(bayes_scores, dtype='float32').reshape(-1)
			li    = np.asarray(li_scores,    dtype='float32').reshape(-1)

			# --------------------------------------------------
			# 2. Bayes = hard / soft mask (PRIOR)
			# --------------------------------------------------
			# Hard mask (minimal, interpretable)
			bayes_prior = np.clip(bayes, 0.0, 1.0)

			# --------------------------------------------------
			# 3. LI = normalized landscape (ENERGY)
			# --------------------------------------------------
			li_norm = li - li.min()
			if li_norm.max() > 0:
				li_norm = li_norm / li_norm.max()

			# --------------------------------------------------
			# 4. Effective landscape: LI | Bayes
			# --------------------------------------------------
			effective = li_norm * bayes_prior

			self._print_scores(
				texts        = texts,
				bayes_scores = bayes_scores,
				li_scores    = li_scores,
				effective    = effective
			)

			# --------------------------------------------------
			# 5. Diagnostics (optional but useful)
			# --------------------------------------------------
			Viz.histogram(bayes,     title='Bayes Scores')
			Viz.histogram(li_norm,   title='LI (normalized)')
			Viz.histogram(effective, title='Effective LI | Bayes')

			exit()

			# --------------------------------------------------
			# 6. Ridge detection (percentile over non-zero)
			# --------------------------------------------------
			nonzero = effective[effective > 0]

			if nonzero.size > 0:
				threshold = np.percentile(nonzero, 90)

				for i, s in enumerate(effective):
					if s >= threshold:
						ridges.append({
							'text':  texts[i],
							'score': float(s)
						})

		return ridges

	
	# Delete chunks and remove vectors from Vdb
	# ----------------------------------------------------------------------
	def _delete_chunks(self, domain, rows):
		for row in rows:
			self.vdb.remove(domain, row.id)
			row.delete()
		return None
	
	# Create and index chunks
	# ----------------------------------------------------------------------
	def _create_chunks_for_document(self, domain, document_id, text, key):
		chunk_texts = self.sentencizer.to_sentences(text)
		if chunk_texts:
			rows = RagDocumentChunk.create_many_for_document(
				document_id=document_id, texts=chunk_texts
			)

			if rows:
				embeddings = self.vdb.encoder.encode_sequence(chunk_texts)
				vecs       = Norm.to_sphere(embeddings).cpu().numpy().astype('float32')
				# for row, vec in tqdm(zip(rows, vecs), desc='    ', total=len(rows)):
				for row, vec in zip(rows, vecs):
					row.vector = vec.tobytes()

				ids = [r.id for r in rows]
				self.vdb.add_many(domain, ids, vectors=vecs)
		return None
	
	# Rerank ridges
	# ----------------------------------------------------------------------
	def _rerank_ridges(self, query, ridge_texts, top_k):
		return self.reranker.rerank(query, ridge_texts, self.reranker.CROSS_ENCODER)[:top_k]
	
	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================
	
	# Check whether a domain exists and has any documents
	# ----------------------------------------------------------------------
	def has_domain(self, domain):
		rows = RagDocument.get_by_domain(domain)          # Fetch documents for domain
		exists = bool(rows)                               # Domain exists if any rows found
		return exists

	# Add or update a document and chunks
	# ----------------------------------------------------------------------
	def add(self, domain, key, text, external_mtime):
		is_added = False
		doc      = RagDocument.get_by_domain_and_key(domain, key)

		if doc is None:
			doc = RagDocument(domain=domain, key=key, mtime=external_mtime).add()
			self._create_chunks_for_document(domain, doc.id, text, key)
			is_added = True
		else:
			if external_mtime > doc.mtime:
				doc.mtime = external_mtime
				self._reindex(domain, doc.id, text, key)
				is_added = True

		return is_added

	# Remove documents and chunks
	# ----------------------------------------------------------------------
	def remove(self, domain, keys=None):
		record_ids = self._get_ids(domain, keys)

		if record_ids:
			rows = RagDocumentChunk.get_by_document_ids(record_ids)
			self._delete_chunks(domain, rows)
			RagDocument.delete_by_ids(record_ids)

		return None

	# Search
	# ----------------------------------------------------------------------
	def search(self, query, domain, keys=None, k=5, ap_prev=None, karma=0.5):
		print(f'Search for domain {domain}')
		result        = []
		document_rows = RagDocument.get_by_domain(domain)
		print(f'Found {len(document_rows)} rows')

		if document_rows:
			ridges = []

			for doc in document_rows:
				chunks = RagDocumentChunk.get_by_document_ids([doc.id])

				if chunks:
					texts = [c.text for c in chunks]

					new_ridges = self._get_ridges(
						query   = query,
						texts   = texts,
						ap_prev = ap_prev,
						karma   = karma
					)

					if new_ridges:
						ridges.extend(new_ridges)

			if ridges:
				ridge_texts = [ridge['text'] for ridge in ridges]
				result = self._rerank_ridges(query, ridge_texts, k)

		print('result', result)

		return result
