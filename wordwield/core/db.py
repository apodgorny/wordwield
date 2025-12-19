# ======================================================================
# Database models for graph edges and RAG documents/chunks.
# ======================================================================

import os
import uuid
from datetime                       import date, datetime
from typing                         import Any, Dict

from sqlalchemy                     import Column, DateTime, Integer, LargeBinary, String, Text, UniqueConstraint, func
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


class RagDocument(Record):
	__tablename__ = 'rag_records'
	__table_args__ = (UniqueConstraint('domain', 'key'),)

	id      = Column(Integer, primary_key=True)                   # object id
	domain  = Column(String,  nullable=False)                     # 'expertise', 'web', 'notes', ...
	key     = Column(String,  nullable=False)                     # identifier inside domain
	mtime   = Column(Integer, nullable=False)                     # rag-level modification time
	created = Column(DateTime, default=datetime.utcnow)           # created timestamp


	# Get document by domain and key
	# ----------------------------------------------------------------------
	@classmethod
	def get_by_domain_and_key(cls, domain, key):
		result = cls.session.query(cls).filter_by(domain=domain, key=key).first()
		return result

	# Get document IDs by keys
	# ----------------------------------------------------------------------
	@classmethod
	def get_ids_by_keys(cls, domain, keys):
		rows = (
			cls.session.query(cls)
			.filter(cls.domain == domain)
			.filter(cls.key.in_(keys))
			.all()
		)
		result = [row.id for row in rows]
		return result

	# Get documents by domain
	# ----------------------------------------------------------------------
	@classmethod
	def get_by_domain(cls, domain):
		result = cls.session.query(cls).filter(cls.domain == domain).all()
		return result

	# Delete documents by IDs
	# ----------------------------------------------------------------------
	@classmethod
	def delete_by_ids(cls, ids):
		rows = cls.session.query(cls).filter(cls.id.in_(ids)).all()
		for row in rows:
			cls.session.delete(row)
		return rows

	# Represent document as string
	# ----------------------------------------------------------------------
	def __repr__(self):
		result = f'<RagDocument #{self.id} type={self.domain} key={self.key}>'
		return result


class RagDocumentChunk(Record):
	__tablename__ = 'rag_chunk_records'

	id          = Column(Integer, primary_key=True)              # chunk id == faiss id
	document_id = Column(Integer, index=True, nullable=False)    # parent RAGDocument
	text        = Column(Text, nullable=False)                   # chunk text
	vector      = Column(LargeBinary, nullable=True)             # serialized vector for rebuilds
	created     = Column(DateTime, default=datetime.utcnow)      # creation timestamp

	# Get chunks by document IDs
	# ----------------------------------------------------------------------
	@classmethod
	def get_by_document_ids(cls, document_ids):
		result = (
			cls.session.query(cls)
			.filter(cls.document_id.in_(document_ids))
			.all()
		)
		return result

	# Get chunks by IDs
	# ----------------------------------------------------------------------
	@classmethod
	def get_by_ids(cls, chunk_ids):
		result = cls.session.query(cls).filter(cls.id.in_(chunk_ids)).all()
		return result

	# Get ID range by document ID
	# ----------------------------------------------------------------------
	@classmethod
	def get_id_range_by_document_id(cls, document_id):
		query = (
			cls.session.query(func.min(cls.id), func.max(cls.id))
			.filter(cls.document_id == document_id)
		)
		result = query.first()
		return result

	# Get document ID range as Python range
	# ----------------------------------------------------------------------
	@classmethod
	def get_document_id_range(cls, document_id):
		min_id, max_id = cls.get_id_range_by_document_id(document_id)
		result = None
		if min_id is not None and max_id is not None:
			result = range(min_id, max_id + 1)
		return result

	# Create many chunks for a document
	# ----------------------------------------------------------------------
	@classmethod
	def create_many_for_document(cls, document_id, texts):
		rows = []
		for text in texts:
			row = cls(document_id=document_id, text=text)
			cls.session.add(row)
			rows.append(row)
		cls.session.flush()
		return rows

	# Delete chunks by IDs
	# ----------------------------------------------------------------------
	@classmethod
	def delete_by_ids(cls, chunk_ids):
		rows = cls.session.query(cls).filter(cls.id.in_(chunk_ids)).all()
		for row in rows:
			cls.session.delete(row)
		return rows

	# Represent chunk as string
	# ----------------------------------------------------------------------
	def __repr__(self):
		result = f'<RagDocumentChunk #{self.id} doc={self.document_id}>'
		return result
