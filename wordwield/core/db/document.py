# ======================================================================
# Document key registry (id → human key).
# ======================================================================

from datetime import datetime

from sqlalchemy import (
	Column,
	DateTime,
	Integer,
	Text,
	CheckConstraint,
	UniqueConstraint,
)

from wordwield.core.base.record import Record



class Document(Record):
	__tablename__ = 'document_keys'

	id      = Column(Integer,  primary_key=True)         # 16-bit doc_id (part of Vid)
	key     = Column(Text,     nullable=False)           # url / path / slug
	meta    = Column(Text,     nullable=True)            # optional json/text
	created = Column(DateTime, default=datetime.utcnow)  # document time of creation

	__table_args__ = (
		CheckConstraint('id >= 0 AND id < 65536', name='ck_document_keys_id_16bit'),
		UniqueConstraint('key', name='uq_document_keys_key'),
	)

	def __repr__(self):
		return f'<DocumentKey id={self.id} key={self.key}>'

	# Get by key
	# ----------------------------------------------------------------------
	@classmethod
	def get(cls, key: str):
		return cls.session.query(cls).filter_by(key=key).first()

	# Create or return existing id
	# ----------------------------------------------------------------------
	@classmethod
	def set(cls, key: str, id: int | None = None, meta: str | None = None) -> int:
		existing = cls.get(key)
		if existing:
			return int(existing.id)

		if id is None:
			max_id = cls.session.query(cls.id).order_by(cls.id.desc()).first()
			next_id = int(max_id[0]) + 1 if max_id else 0
			id = next_id

		if id < 0 or id > 0xFFFF:
			raise ValueError('Document id must fit in 16 bits')

		row = cls(id=id, key=key, meta=meta)
		cls.session.add(row)
		cls.session.flush()
		return int(row.id)
