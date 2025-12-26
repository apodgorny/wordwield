# ======================================================================
# Database models for graph edges and RAG documents/chunks.
# ======================================================================

from datetime import datetime

from sqlalchemy import (
	UniqueConstraint,
	Column,
	DateTime,
	Integer,
	String,
)

from wordwield.core.base.record import Record


class EdgeRecord(Record):
	__tablename__ = 'edges'
	__table_args__ = (
		UniqueConstraint('id1', 'id2', 'key1', 'key2', 'rel1', 'rel2', 'type1', 'type2'),
	)

	id      = Column(Integer, primary_key=True)	            # Unique identifier of this edge row
	id1     = Column(Integer, nullable=False)	            # ID of the source object (the 'from' side of the edge)
	type1   = Column(String,  nullable=False)	            # Class name (string) of the source object
	id2     = Column(Integer, nullable=False)	            # ID of the target object (the 'to' side of the edge)
	type2   = Column(String,  nullable=False)	            # Class name (string) of the target object
	rel1    = Column(String,  nullable=False, default='')  # Field name (attribute) on the source object which defines this relation
	rel2    = Column(String,  nullable=False, default='')  # Field name (attribute) on the target object that is considered a reverse relation (if exists)
	key1    = Column(String,  nullable=False, default='')  # Key/index for the source (used for List/Dict: list index or dict key; empty for direct relations)
	key2    = Column(String,  nullable=False, default='')  # Key/index for the target (used for List/Dict on the reverse side; usually empty)
	created = Column(DateTime, default=datetime.utcnow)    # Timestamp when this edge record was created (UTC)

	# Represent edge as string
	# ----------------------------------------------------------------------
	def __repr__(self):
		key1 = f'[{self.key1}]' if self.key1 else ''
		key2 = f'[{self.key2}]' if self.key2 else ''
		rel1 = f'.{self.rel1}' if self.rel1 else ''
		rel2 = f'.{self.rel2}' if self.rel2 else ''
		result = f'Edge #{self.id}: {self.type1}{rel1}{key1}({self.id1}) -> {self.type2}{rel2}{key2}({self.id2})'
		return result


# ======================================================================
# ======================================================================
# ======================================================================


# class RagDocumentChunk(Record):
# 	__tablename__ = 'rag_document_chunk'

# 	id          = Column(Integer, primary_key=True)              # chunk id == faiss id
# 	document_id = Column(Integer, index=True, nullable=False)    # parent RAGDocument
# 	text        = Column(Text, nullable=False)                   # chunk text
# 	vector      = Column(LargeBinary, nullable=True)             # serialized vector for rebuilds
# 	created     = Column(DateTime, default=datetime.utcnow)      # creation timestamp
# 	_vector     = None                                           # cached deserialized vector

# 	@classmethod
# 	def group_ids_by_document(cls, domain, ids):
# 		if not ids:
# 			return {}

# 		rows = (
# 			cls.session.query(cls.document_id, cls.id)
# 			.join(RagDocument, cls.document_id == RagDocument.id)
# 			.filter(cls.id.in_(ids))
# 		)
# 		if domain is not None:
# 			rows = rows.filter(RagDocument.domain == domain)

# 		rows = rows.all()
# 		result = defaultdict(list)
# 		for row in rows:
# 			doc_id, chunk_id = row
# 			result[doc_id].append(chunk_id)
# 		return dict(result)

# 	# Get chunks by document IDs
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def get_by_document_ids(cls, document_ids):
# 		result = []
# 		if document_ids:
# 			result = (
# 				cls.session.query(cls)
# 				.filter(cls.document_id.in_(document_ids))
# 				.all()
# 			)
# 		return result

# 	# Create many chunks for a document
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def create_many(cls, document_id, texts, vectors):
# 		rows = []
# 		for text, vector in zip(texts, vectors):
# 			row = cls(
# 				document_id = document_id,
# 				text        = text,
# 				vector      = vector_serialize(vector)
# 			)
# 			cls.session.add(row)
# 			rows.append(row)
# 		cls.session.flush()
# 		return [row.id for row in rows]

# 	# Delete chunks by document IDs
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def delete_by_document_ids(cls, document_ids):
# 		if not document_ids:
# 			return []
# 		rows = cls.session.query(cls).filter(cls.document_id.in_(document_ids)).all()
# 		for row in rows:
# 			cls.session.delete(row)
# 		return rows

# 	# Represent chunk as string
# 	# ----------------------------------------------------------------------
# 	def __repr__(self):
# 		result = f'<RagDocumentChunk #{self.id} doc={self.document_id}>'
# 		return result

# 	@property
# 	def tensor(self):
# 		if self._vector is None and self.vector is not None:
# 			self._vector = vector_deserialize(self.vector)
# 		return self._vector


# # ======================================================================
# # ======================================================================
# # ======================================================================


# class RagDocument(Record):
# 	__tablename__ = 'rag_document'
# 	__table_args__ = (UniqueConstraint('domain', 'key'),)

# 	id        = Column(Integer,  primary_key=True)          # object id
# 	domain    = Column(String,   nullable=False)            # 'expertise', 'web', 'notes', ...
# 	key       = Column(String,   nullable=False)            # identifier inside domain
# 	mtime     = Column(Integer,  nullable=False)            # rag-level modification time
# 	created   = Column(DateTime, default=datetime.utcnow)   # created timestamp
# 	temporary = Column(Boolean,  default=True)              # will the document load to faiss or be erased on restart

# 	# Dump all data for faiss
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def get_all(cls, document_ids=None):
# 		'''
# 			Return mapping:
# 				{
# 					domain: {
# 						doc_id: {
# 							chunk_id: {
# 								vector : vector_tensor,
# 								text   : chunk_text
# 							}
# 						}
# 					}
# 				}
# 			Vectors are already deserialized into float32 torch tensors.
# 			Only non-temporary documents are included.
# 		'''
# 		query = (
# 			cls.session.query(cls, RagDocumentChunk)
# 			.outerjoin(RagDocumentChunk, RagDocumentChunk.document_id == cls.id)
# 			.filter(cls.temporary == False)
# 		)
# 		if document_ids:
# 			query = query.filter(cls.id.in_(document_ids))

# 		rows = query.all()

# 		result = defaultdict(lambda: defaultdict(dict))
# 		for doc, chunk in rows:
# 			doc_dict = result[doc.domain][doc.id]  # ensure doc bucket exists
# 			if chunk:
# 				doc_dict[chunk.id] = {
# 					'vector' : vector_deserialize(chunk.vector),
# 					'text'   : chunk.text
# 				}

# 		# Convert nested defaultdicts to plain dicts for a clean return value
# 		return {
# 			domain: {doc_id: dict(chunks) for doc_id, chunks in docs.items()}
# 			for domain, docs in result.items()
# 		}

# 	# Get document id by document key
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def keys_to_ids(cls, domain, keys):
# 		if keys is None:
# 			return [row.id for row in cls.get_by_domain(domain)]
# 		rows = cls.session.query(cls).filter(
# 			cls.domain == domain, 
# 			cls.key.in_(keys)
# 		).all()
# 		return [row.id for row in rows]

# 	# Get document IDs for a domain (optionally filtered by keys)
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def get_ids(cls, domain, keys=None):
# 		if keys is None:
# 			return [doc.id for doc in cls.get_by_domain(domain)]
# 		return cls.keys_to_ids(domain, keys)
	
# 	# Get document by domain and key
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def get(cls, domain, key):
# 		return cls.session.query(cls).filter_by(
# 			domain = domain,
# 			key    = key
# 		).first()

# 	# Get all documents for a domain
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def get_by_domain(cls, domain):
# 		return cls.session.query(cls).filter(cls.domain == domain).all()
	
# 	# Delete documents by IDs
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def delete_by_id(cls, id):
# 		document = cls.session.query(cls).filter(cls.id == id).first()
# 		cls.session.delete(document)
# 		RagDocumentChunk.delete_by_document_ids([id])

# 	# Delete multiple documents by IDs
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def delete_by_ids(cls, ids):
# 		if not ids:
# 			return []
# 		for doc_id in ids:
# 			cls.delete_by_id(doc_id)
# 		return ids

# 	# Delete all temporary documents (and their chunks)
# 	# ----------------------------------------------------------------------
# 	@classmethod
# 	def delete_temporary(cls):
# 		docs = cls.session.query(cls).filter(cls.temporary == True).all()
# 		deleted = []
# 		for doc in docs:
# 			cls.delete_by_id(doc.id)
# 			deleted.append(doc.id)
# 		return deleted


# 	# Represent document as string
# 	# ----------------------------------------------------------------------
# 	def __repr__(self):
# 		result = f'<RagDocument #{self.id} type={self.domain} key={self.key}>'
# 		return result
