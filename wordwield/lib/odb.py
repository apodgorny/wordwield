from sqlalchemy          import inspect
from sqlalchemy.orm      import Session

from typing                    import get_origin, List, Dict
from wordwield.lib.transform   import T
from wordwield.lib.edge        import Edge
from wordwield.db              import EdgeRecord



class ODB:

	session = None
	types   = {}
	objects = {}

	# Class methods
	################################################################################################

	@classmethod
	def load(cls, id_or_name: int | str, o_class: 'O') -> 'O':
		if isinstance(id_or_name, int):
			return cls.load_by_id(id_or_name, o_class)
		if isinstance(id_or_name, str):
			return cls.load_by_name(id_or_name, o_class)
		return None

	@classmethod
	def load_by_id(cls, id: int, o_class: 'O') -> 'O':
		if isinstance(o_class, str):
			o_class = cls.types[o_class]

		key  = (o_class, id)
		if key in cls.objects:
			return cls.objects[key]
		
		o         = cls._preload(id, o_class)
		o.__db__  = ODB(o)
		o.__id__  = id

		cls.objects[key] = o

		o.db._load_edges()
		return o

	@classmethod
	def load_by_name(cls, name: str, o_class: 'O') -> 'O':
		record = cls.session.query(EdgeRecord).filter_by(
			type1 = 'global',
			id1   = 0,
			rel1  = 'ref',
			key1  = name,
		).first()

		if record:
			return cls.load(record.id2, o_class)
		return None

	@classmethod
	def _preload(cls, id, o_class):
		'''Loads simple data items and stubs for O, list[O] and dict[str, O]'''
		orm_class = T(T.PYDANTIC, T.SQLALCHEMY_MODEL, o_class)
		orm_obj   = cls.session.get(orm_class, id)

		if not orm_obj:
			raise ValueError(f'{o_class.__name__} with id={id} not found')

		data = T(T.SQLALCHEMY_MODEL, T.DATA, orm_obj)
		data.pop('id')
		return o_class.model_construct(**data)

	def _reload(self):
		o     = self._o
		oid   = o.id
		otype = type(o)

		if not oid:
			raise ValueError(f'Cannot reload object of type {otype.__name__} without id')

		new = otype.load(oid)
		for name in o.model_fields:
			setattr(o, name, getattr(new, name, None))
		o.__db__ = self

	def _reload_related(self):
		o = self._o

		for other in list(ODB.objects.values()):
			if not isinstance(other, O): continue

			for name, field in other.model_fields.items():
				kind, _ = other.get_field_kind(name, field.annotation)
				value   = getattr(other, name, None)

				if kind == 'single':
					if value is o:
						other.db._reload()
						break

				elif kind == 'list' and isinstance(value, list):
					if any(item is o for item in value):
						other.db._reload()
						break

				elif kind == 'dict' and isinstance(value, dict):
					if any(item is o for item in value.values()):
						other.db._reload()
						break

	# Magic methods
	################################################################################################

	def __init__(self, instance: 'O'):
		self._o          = instance
		self._orm_class  = T(T.PYDANTIC, T.SQLALCHEMY_MODEL, type(instance))
		self._edge       = Edge(self.session)
		self._is_deleted = False

	def __getattr__(self, name): return getattr(self.session, name)

	# Private
	################################################################################################

	def _o_or_none(self, obj):
		if isinstance(obj, type(self._o)):
			return obj
		return None

	def _load_edges(self, seen=None):
		o    = self._o
		seen = seen or set()
		key  = (type(o), o.id)

		if key not in seen:
			seen.add(key)
			for name, field in o.model_fields.items():
				if not name in o.__dict__:
					value = self.get_related(name)
					if value is None:
						kind, _ = o.get_field_kind(name)
						if   kind == 'list' : value = []
						elif kind == 'dict' : value = {}
						else                : value = None

					setattr(o, name, value)
					val = getattr(o, name)
					if isinstance(val, list):
						for item in val:
							if hasattr(item, 'db'):
								item.db._load_edges(seen)
					elif hasattr(val, 'db'):
						val.db._load_edges(seen)

	def _save_edges(self):
		o = self._o
		s = self.session

		for name, field in o.model_fields.items():
			val         = getattr(o, name, None)
			kind, inner = o.get_field_kind(name, field.annotation)
			reverse     = field.json_schema_extra.get('reverse') if field.json_schema_extra else None

			if kind == 'single' and is_valid_edge_target(val):
				self._save_edge(src=o, tgt=val, rel1=name, rel2=reverse)

			elif kind == 'list' and isinstance(val, list):
				for i, item in enumerate(val):
					self._save_edge(src=o, tgt=item, rel1=name, rel2=reverse, key1=str(i))

			elif kind == 'dict' and isinstance(val, dict):
				for k, item in val.items():
					self._save_edge(src=o, tgt=item, rel1=name, rel2=reverse, key1=str(k))

	def _save_edge(self, src, tgt, rel1, rel2, key1='', key2=''):
		if (
			O.is_o_instance(tgt)
			and tgt.id is not None
			and self.session.get(tgt.db._orm_class, tgt.id) is not None
			and not getattr(tgt.db, '_is_deleted', False)
		):
			tgt.save()
			if src.id is not None:
				kwargs = {
					'id1'  : src.id, 'id2'  : tgt.id,
					'rel1' : rel1,   'rel2' : rel2,
					'key1' : key1,   'key2' : key2,
				}
				if not self.edges.update(** kwargs):
					self.edges.create(
						** kwargs,
						type1 = src.__class__.__name__,
						type2 = tgt.__class__.__name__,
					)

	def _set_name(self, name: str):
		if not self._o.id:
			raise ValueError(f'❌ Id is not set in `{name}`')
			
		if name is None or self.get_name() == name:
			return

		if ODB.load_by_name(name, self.__class__):
			raise ValueError(f'❌ Name `{name}` already exists')

		self.edges.set(
			id1   = 0,
			id2   = self._o.id,
			type1 = 'global',
			type2 = self._o.__class__.__name__,
			rel1  = 'ref',
			rel2  = 'ref',
			key1  = name
		)


	# Public
	################################################################################################

	@property
	def edges(self)         : return self._edge

	@property
	def table_name(self)    : return self._orm_class.__tablename__
	
	def query(self)         : return self.session.query(self._orm_class)
	def table_exists(self)  : return inspect(self.session.bind).has_table(self.table_name)
	def create_table(self)  : self._orm_class.metadata.create_all(self.session.bind)
	def drop_table(self)    : self._orm_class.metadata.drop_all(self.session.bind)
	def filter(self, *args) : return self.query().filter(*args)
	def get(self, id)       : return self._o_or_none(self.session.get(self._orm_class, id))
	def first(self)         : return self._o_or_none(self.query().first())
	def count(self)         : return self.query().count()
	def exists(self)        : return self.query().exists().scalar()
	def all(self)           : return [r for r in self.query().all() if isinstance(r, self._orm_class)]
	def refresh(self)       : self.session.refresh(self._o)
	def expunge(self)       : self.session.expunge(self._o)
	def add(self)           : self.session.add(self._o)
	def commit(self)        : self.create_table(); self.session.commit()
	def rollback(self)      : self.session.rollback()
	def flush(self)         : self.session.flush()
	def close(self)         : self.session.close()

	def save(self, name=None):
		data   = self._o.to_dict()
		obj_id = getattr(self._o, '__id__', None)

		self.create_table()

		if obj_id:
			# No need to check for existence – we assume id is valid
			record = self.session.get(self._orm_class, obj_id)
			if not record:
				raise ValueError(f'Record with id={obj_id} not found in table `{self._orm_class.__tablename__}`')
			for key, value in data.items():
				setattr(record, key, value)
		else:
			record = self._orm_class(**data)
			self.session.add(record)

		self._save_edges()
		self.commit()
		setattr(self._o, '__id__', getattr(record, 'id', None))
		self._load_edges()

		if name is not None:
			self._set_name(name)
			self.commit()

		return self

	def delete(self):
		id  = getattr(self._o, 'id', None)
		typ = self._o.__class__.__name__

		if id is not None:
			self.session.query(self.edges.model).filter(
				((self.edges.model.id1 == id) & (self.edges.model.type1 == typ)) |
				((self.edges.model.id2 == id) & (self.edges.model.type2 == typ))
			).delete()

			self.query().filter(self._orm_class.id == id).delete()

		self.commit()
		self._is_deleted = True

	def get_related(self, name: str):
		o      = self._o
		edges  = self.edges.get(o, rel=name)
		result = []

		for edge in edges:
			if edge.rel1 == name and edge.id1 == o.id:
				result.append(ODB.load(edge.id2, edge.type2))

			elif edge.rel2 == name and edge.id2 == o.id:
				result.append(ODB.load(edge.id1, edge.type1))

		# Detect result type by field shape
		field = o.model_fields.get(name)
		if field is None:
			raise AttributeError(f'Field `{name}` not found in {o.__class__.__name__}')
		tp = field.annotation

		if get_origin(tp) in (list, List) : return result
		elif result                       : return result[0]
		else                              : return None

	def get_name(self) -> str:
		for edge in self.edges.get(self._o, rel='ref'):
			if edge.id1 == 0 and edge.type1 == 'global':
				return edge.key1
		return None
