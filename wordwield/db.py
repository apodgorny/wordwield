import os, uuid

from typing                         import Any, Dict
from datetime                       import datetime, date

from dotenv                         import load_dotenv
from sqlalchemy                     import Column, Enum, Integer, String, Text, DateTime, create_engine, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm                 import Mapped, mapped_column, sessionmaker
from sqlalchemy.ext.mutable         import MutableDict
from sqlalchemy.dialects.postgresql import UUID

from wordwield.lib.record           import Record, Base


load_dotenv()

PROJECT_PATH          = os.getenv('PROJECT_PATH')
DB_NAME               = os.getenv('DB_NAME')
DB_URL                = f'sqlite:///./{DB_NAME}.db'
DB_PATH               = os.path.join(PROJECT_PATH, f'{DB_NAME}.db')
engine                = create_engine(DB_URL, connect_args={'check_same_thread': False}, echo=False)
SessionLocal          = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session               = SessionLocal()

if os.path.exists(DB_PATH):
	if not os.access(DB_PATH, os.W_OK):
		raise RuntimeError(f'❌ Cannot write to DB file: `{DB_PATH}` — it is read-only.')


class TypeRecord(Record):
	__tablename__ = 'types'

	name         : Mapped[str]             = mapped_column(String(255),                  primary_key=True, comment='Unique type name (also class name)')
	description  : Mapped[str]             = mapped_column(Text,                         nullable=True,    comment='Optional type description')
	code         : Mapped[str]             = mapped_column(Text,                         nullable=False,   comment='Python source code of the type')

class OperatorRecord(Record):
	__tablename__ = 'operators'

	name         : Mapped[str]             = mapped_column(String(255),                  primary_key=True, comment='Unique operator name')
	class_name   : Mapped[str]             = mapped_column(String(255),                  nullable=False,   comment='Unique operator class name')
	description  : Mapped[str]             = mapped_column(Text,                         nullable=True,    comment='Optional operator description')
	code         : Mapped[str]             = mapped_column(Text,                         nullable=True,    comment='Source code or prompt (or empty for composite)')
	restrict     : Mapped[bool]            = mapped_column(Boolean,                      default=True,     nullable=False, comment='If True, apply interpreter restrictions')
	
	input_type   : Mapped[Dict[str, Any]]  = mapped_column(JSON,                         nullable=False,   comment='Full JSON Schema')
	output_type  : Mapped[Dict[str, Any]]  = mapped_column(JSON,                         nullable=False,   comment='Full JSON Schema')

	scope        : Mapped[Dict[str, Any]]  = mapped_column(MutableDict.as_mutable(JSON), default=dict,     comment='Runtime scope for function operators')
	config       : Mapped[Dict[str, Any]]  = mapped_column(MutableDict.as_mutable(JSON), default=dict,     comment='Configuration passed to interpreter')

class EdgeRecord(Record):
	__tablename__ = 'edges'
	__table_args__ = (
		UniqueConstraint('id1', 'id2', 'key1', 'key2', 'rel1', 'rel2'),
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