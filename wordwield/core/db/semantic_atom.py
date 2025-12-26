# ======================================================================
# Semantic atom sql model and helpers.
# ======================================================================

from datetime import datetime

import numpy as np
import torch
from sqlalchemy import Column, DateTime, Integer, LargeBinary, Text

from wordwield.core.base.record import Record
from wordwield.core.vid         import Vid


def vector_serialize(vector):
	if vector is None:
		return None
	if isinstance(vector, torch.Tensor):
		arr = vector.detach().to(torch.float32).cpu().numpy()
	elif isinstance(vector, np.ndarray):
		arr = vector.astype(np.float32)
	else:
		arr = np.asarray(vector, dtype=np.float32)
	return arr.tobytes()


def vector_deserialize(blob):
	if blob is None:
		return None
	if isinstance(blob, torch.Tensor):
		return blob
	if isinstance(blob, np.ndarray):
		return torch.from_numpy(blob.astype(np.float32))
	if isinstance(blob, (bytes, bytearray, memoryview)):
		arr = np.frombuffer(blob, dtype=np.float32)
		return torch.from_numpy(arr)
	return torch.as_tensor(blob, dtype=torch.float32)


class SemanticAtom(Record):
	__tablename__ = 'semantic_atom'

	id      = Column(Integer,     primary_key=True)   # Canonical int_id
	text    = Column(Text,        nullable=False)
	mtime   = Column(Integer,     nullable=True)
	vector  = Column(LargeBinary, nullable=True)
	created = Column(DateTime,    default=datetime.utcnow)

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Get one atom by address.
	# ----------------------------------------------------------------------
	@classmethod
	def get(cls, vid: Vid | int | None = None):
		result = {}
		query  = cls.session.query(cls)

		if vid is not None:
			v = vid if isinstance(vid, Vid) else Vid(id=vid)
			query = query.filter(*v.conditions(cls.id))

		rows = query.all()

		for row in rows:
			result[int(row.id)] = dict(
				text   = row.text,
				mtime  = row.mtime,
				vector = vector_deserialize(row.vector)
			)
		return result
	
	# Remove one atom by address.
	# ----------------------------------------------------------------------
	@classmethod
	def unset(cls, vid: Vid | int | None = None):
		if vid is None:
			return False

		v = vid if isinstance(vid, Vid) else Vid(id=vid)
		rows = cls.session.query(cls).filter(*v.conditions(cls.id)).all()

		removed = False
		for row in rows:
			cls.session.delete(row)
			removed = True

		return removed

	# Construct and set atom from semantic components.
	# ----------------------------------------------------------------------
	@classmethod
	def set(
		cls,
		vid    : Vid | int,
		text   : str,
		vector,
		mtime  : int | None = None,
	) -> int:
		if vector is None: raise ValueError('Vector can not be None')
		if text   is None: raise ValueError('Text can not be None')
		
		id  = vid.id if isinstance(vid, Vid) else Vid(id=vid).id

		row = cls(
			id     = id,
			text   = text,
			mtime  = mtime,
			vector = vector_serialize(vector)
		)
		cls.session.merge(row)
		return id