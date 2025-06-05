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

	def _update(self, id1, id2, rel1, rel2, key1='', key2='') -> bool:
		q = self.session.query(self.model)

		candidates = q.filter(
			self._get_filter(id1, id2, rel1, rel2)
		).all()

		for edge in candidates:
			updated = False

			if not edge.key1:
				if edge.id1 == id1 and key1:
					edge.key1 = key1
					updated   = True
				elif edge.id1 == id2 and key2:
					edge.key1 = key2
					updated   = True

			if not edge.key2:
				if edge.id2 == id2 and key2:
					edge.key2 = key2
					updated   = True
				elif edge.id2 == id1 and key1:
					edge.key2 = key1
					updated   = True

			if updated:
				self.session.add(edge)
				return True

		return False

	def _get_filter(self, id1, id2, rel1, rel2):
		return or_(
			and_(
				self.model.id1  == id1,  self.model.id2  == id2,
				self.model.rel1 == rel1, self.model.rel2 == rel2
			),
			and_(
				self.model.id1  == id2,  self.model.id2  == id1,
				self.model.rel1 == rel2, self.model.rel2 == rel1
			)
		)

	# Public methods
	############################################################################

	def set(self, id1, id2, type1, type2, rel1, rel2, key1='', key2=''):
		if not self._update(id1, id2, rel1, rel2, key1, key2):
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
