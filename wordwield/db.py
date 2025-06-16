import os, uuid

from typing                         import Any, Dict
from datetime                       import datetime, date

from dotenv                         import load_dotenv
from sqlalchemy                     import Column, Enum, Integer, String, Text, DateTime, create_engine, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm                 import Mapped, mapped_column, sessionmaker
from sqlalchemy.ext.mutable         import MutableDict
from sqlalchemy.dialects.postgresql import UUID

from wordwield.lib.record           import Record


class EdgeRecord(Record):
	__tablename__ = 'edges'
	__table_args__ = (
		UniqueConstraint('id1', 'id2', 'key1', 'key2', 'rel1', 'rel2', 'type1', 'type2'),
	)

	id      = Column(Integer, primary_key=True)	          # Unique identifier of this edge row
	id1     = Column(Integer, nullable=False)	          # ID of the source object (the "from" side of the edge)
	type1   = Column(String, nullable=False)	          # Class name (string) of the source object
	id2     = Column(Integer, nullable=False)	          # ID of the target object (the "to" side of the edge)
	type2   = Column(String, nullable=False)	          # Class name (string) of the target object
	rel1    = Column(String, nullable=False, default='')  # Field name (attribute) on the source object which defines this relation
	rel2    = Column(String, nullable=False, default='')  # Field name (attribute) on the target object that is considered a reverse relation (if exists)
	key1    = Column(String, nullable=False, default='')  # Key/index for the source (used for List/Dict: list index or dict key; empty for direct relations)
	key2    = Column(String, nullable=False, default='')  # Key/index for the target (used for List/Dict on the reverse side; usually empty)
	created = Column(DateTime, default=datetime.utcnow)   # Timestamp when this edge record was created (UTC)

	def __repr__(self):
		key1 = f'[{self.key1}]' if self.key1 else ''
		key2 = f'[{self.key2}]' if self.key2 else ''
		rel1 = f'.{self.rel1}'  if self.rel1 else ''
		rel2 = f'.{self.rel2}'  if self.rel2 else ''
		return f'Edge #{self.id}: {self.type1}{rel1}{key1}({self.id1}) -> {self.type2}{rel2}{key2}({self.id2})'