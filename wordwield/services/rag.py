# ==================================================
# RAG orchestration: DB CRUD, chunking, and FAISS sync.
# ==================================================

import numpy as np

from tqdm                             import tqdm

from wordwield.lib.base.service       import Service
from wordwield.lib.db                 import RagDocument, RagDocumentChunk
from wordwield.lib.norm               import Norm
from wordwield.lib.sentensizers.pysbd import SentensizerPysbd as Sentensizer
from wordwield.lib.vdb                import Vdb



class Rag(Service):

	def initialize(self):
		self.vdb         = Vdb()
		self.sentensizer = Sentensizer()

	# ==================================================
	# PRIVATE METHODS
	# ==================================================

	# Delete chunks and remove vectors from Vdb
	# --------------------------------------------------
	def _delete_chunks(self, domain, rows):
		for row in rows:
			self.vdb.remove(domain, row.id)
			row.delete()
		return None

	# Remove all chunks belonging to a document
	# --------------------------------------------------
	def _remove_record_chunks(self, domain, record_id):
		rows = RagDocumentChunk.get_by_document_ids([record_id])
		self._delete_chunks(domain, rows)
		return None

	# Create and index chunks
	# --------------------------------------------------
	def _create_chunks_for_document(self, domain, document_id, text, key):
		print(f'    Indexing `{domain}:{key}`')
		chunk_texts = self.sentensizer.to_sentences(text)
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

	# Reindex a document fully
	# --------------------------------------------------
	def _reindex(self, domain, record_id, text, key):
		self._remove_record_chunks(domain, record_id)
		self._create_chunks_for_document(domain, record_id, text, key)
		return None

	# Resolve document IDs for a domain and optional keys
	# --------------------------------------------------
	def _get_ids_by_keys_and_domain(self, domain, keys=None):
		record_ids = []
		if keys is None:
			record_rows = RagDocument.get_by_domain(domain)
			record_ids  = [r.id for r in record_rows]
		else:
			record_ids  = RagDocument.get_ids_by_keys(domain, keys)
		return record_ids

	# Rebuild a domain index from stored vectors
	# --------------------------------------------------
	def _rebuild_domain_index(self, domain):
		doc_rows = RagDocument.get_by_domain(domain)
		doc_ids  = [r.id for r in doc_rows]
		if doc_ids:
			chunk_rows = RagDocumentChunk.get_by_document_ids(doc_ids)

			ids  = []
			vecs = []
			for row in chunk_rows:
				has_vector   = row.vector is not None
				vec          = np.frombuffer(row.vector, dtype='float32') if has_vector else None
				is_valid_dim = vec is not None and vec.size == self.vdb.dim
				if is_valid_dim:
					ids.append(row.id)
					vecs.append(vec)

			if vecs:
				self.vdb.add_many(domain, ids, vectors=np.stack(vecs))
		return None

	# Filter chunk rows to allowed document IDs and order by found_ids
	# --------------------------------------------------
	def _filter_chunks_by_ids(self, chunk_rows, record_ids, found_ids):
		allowed_ids = set(record_ids)
		id_to_chunk = {
			c.id: c for c in chunk_rows
			if c.document_id in allowed_ids
		}
		result = [id_to_chunk[i] for i in found_ids if i in id_to_chunk]
		return result

	# Build contextual text groups for expanded IDs
	# --------------------------------------------------
	def _get_texts(self, found_ids, record_ids, margin, doc_to_ids, id_to_doc):
		id_groups    = self._expand_ids(found_ids, margin=margin, doc_to_ids=doc_to_ids, id_to_doc=id_to_doc)
		texts        = []
		all_ids_flat = [i for group in id_groups for i in group]
		chunk_rows   = RagDocumentChunk.get_by_ids(all_ids_flat)
		filtered     = self._filter_chunks_by_ids(chunk_rows, record_ids, all_ids_flat)
		id_to_chunk  = {c.id: c for c in filtered}

		for group in id_groups:
			group_texts = [id_to_chunk[i].text for i in group if i in id_to_chunk]
			if group_texts:
				texts.append('\n'.join(group_texts))

		return texts

	# Expand found chunk IDs with contextual margins
	# --------------------------------------------------
	def _expand_ids(self, found_ids, margin, doc_to_ids, id_to_doc):
		if margin <= 0:
			return [[fid] for fid in found_ids]

		expanded = []

		for fid in found_ids:
			doc_id = id_to_doc.get(fid)
			if doc_id is None or doc_id not in doc_to_ids:
				continue
			id_list = doc_to_ids[doc_id]
			try:
				pos = id_list.index(fid)
			except ValueError:
				continue
			start = max(0, pos - margin)
			end   = min(len(id_list), pos + margin + 1)
			expanded.append(id_list[start:end])

		return expanded

	# ==================================================
	# PUBLIC METHODS
	# ==================================================

	# Add or update a document and chunks
	# --------------------------------------------------
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
	# --------------------------------------------------
	def remove(self, domain, keys=None):
		record_ids = self._get_ids_by_keys_and_domain(domain, keys)

		if record_ids:
			rows = RagDocumentChunk.get_by_document_ids(record_ids)
			self._delete_chunks(domain, rows)
			RagDocument.delete_by_ids(record_ids)

		return None

	# Search chunks using vector query
	# --------------------------------------------------
	def search(self, domain, query, keys=None, k=5, margin=2, ap_prev=None, karma=0.5):
		texts      = []
		ap_next    = ap_prev
		record_ids = self._get_ids_by_keys_and_domain(domain, keys)

		if record_ids:
			if self.vdb.domain_size(domain) == 0:
				self._rebuild_domain_index(domain)

			doc_chunks = RagDocumentChunk.get_by_document_ids(record_ids)
			doc_to_ids = {}
			id_to_doc  = {}

			for c in doc_chunks:
				doc_to_ids.setdefault(c.document_id, []).append(c.id)
				id_to_doc[c.id] = c.document_id

			for ids in doc_to_ids.values():
				ids.sort()

			id_range = None

			if keys is not None and len(record_ids) == 1:
				id_range = RagDocumentChunk.get_document_id_range(record_ids[0])

			found_ids, ap_next = self.vdb.query(
				domain     = domain,
				text       = query,
				k          = k,
				id_range   = id_range,
				ap_prev    = ap_prev,
				karma      = karma
			)

			if found_ids:
				texts = self._get_texts(found_ids, record_ids, margin, doc_to_ids, id_to_doc)

		return texts, ap_next

	# Identify document IDs for keys
	# --------------------------------------------------
	def identify(self, domain, keys):
		result = RagDocument.get_ids_by_keys(domain, keys)
		return result
