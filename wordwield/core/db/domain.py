# ======================================================================
# Domain registry (human → numeric).
# ======================================================================

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Text, CheckConstraint

from wordwield.core.base.record import Record



class Domain(Record):
	__tablename__ = 'domains'

	id      = Column(Integer,  primary_key=True)            # 16-bit domain id
	name    = Column(Text,     nullable=False, unique=True) # domain name
	meta    = Column(Text,     nullable=True)               # optional json/text
	created = Column(DateTime, default=datetime.utcnow)     # domain time of creation

	__table_args__ = (
		CheckConstraint('id >= 0 AND id < 65536', name='ck_domains_id_16bit'),
	)

	def __repr__(self):
		return f'<Domain id={self.id} name={self.name}>'

	# Get by name
	# ----------------------------------------------------------------------
	@classmethod
	def get(cls, name: str):
		return cls.session.query(cls).filter_by(name=name).first()

	# Create or return existing id
	# ----------------------------------------------------------------------
	@classmethod
	def set(cls, name: str, id: int | None = None, meta: str | None = None) -> int:
		existing = cls.get(name)
		if existing:
			return int(existing.id)

		if id is None:
			# allocate next available id (simple monotonic allocator)
			max_id = cls.session.query(cls.id).order_by(cls.id.desc()).first()
			next_id = int(max_id[0]) + 1 if max_id else 0
			id = next_id

		if id < 0 or id > 0xFFFF:
			raise ValueError('Domain id must fit in 16 bits')

		row = cls(id=id, name=name, meta=meta)
		cls.session.add(row)
		cls.session.flush()
		return int(row.id)

	# List all domains
	# ----------------------------------------------------------------------
	@classmethod
	def get_all(cls):
		return cls.session.query(cls).all()
