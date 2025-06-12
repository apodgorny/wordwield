from typing import Any

from sqlalchemy import and_, or_

from wordwield.db import EdgeRecord


class Edge:
	def __init__(self, session):
		self.session = session
		self.model   = EdgeRecord

	# Private methods
	############################################################################

	def _create(self, id1, id2, type1, type2, rel1, rel2, key1='', key2=''):
		record = self.model(
			id1   = id1,
			id2   = id2,
			type1 = type1,
			type2 = type2,
			rel1  = rel1,
			rel2  = rel2,
			key1  = key1,
			key2  = key2
		)
		self.session.add(record)

	def _update(self, id1, id2, type1, type2, rel1, rel2, key1='', key2='') -> bool:
		q = self.session.query(self.model)
		candidates = q.filter(
			self._get_filter(id1, id2, type1, type2, rel1, rel2, key1, key2)
		).all()
		if candidates:
			# Тут можно обновить другие поля, если надо (например, время обновления)
			return True
		return False

	def _get_filter(self, id1, id2, type1, type2, rel1, rel2, key1, key2):
		return and_(
			self.model.id1   == id1,
			self.model.id2   == id2,
			self.model.type1 == type1,
			self.model.type2 == type2,
			self.model.rel1  == rel1,
			self.model.rel2  == rel2,
			self.model.key1  == key1,
			self.model.key2  == key2,
		)

	# Public methods
	############################################################################

	def set(self, id1, id2, type1, type2, rel1, rel2, key1='', key2=''):

		key1 = str(key1) if key1 is not None else ''
		key2 = str(key2) if key2 is not None else ''

		updated = self._update(id1, id2, type1, type2, rel1, rel2, key1, key2)
		if not updated:
			self._create(id1, id2, type1, type2, rel1, rel2, key1, key2)

	def unset(self, id1, id2, rel1, rel2):
		self.session.query(self.model).filter(
			self._get_filter(id1, id2, rel1, rel2)
		).delete()

	def get(self, obj: Any, rel: str = None):
		query = self.session.query(EdgeRecord).filter(
			(EdgeRecord.id1 == obj.id) | (EdgeRecord.id2 == obj.id)
		)
		if rel is not None:
			query = query.filter(
				(EdgeRecord.rel1 == rel) | (EdgeRecord.rel2 == rel)
			)
		return query.all()
