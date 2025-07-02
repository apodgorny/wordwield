from sqlalchemy                import inspect
from sqlalchemy.orm            import Session
from sqlalchemy.exc            import IntegrityError

from pydantic_core             import PydanticUndefined

from typing                    import get_origin, List, Dict
from wordwield.lib.predicates  import is_list, is_dict
from wordwield.lib.t           import T
from wordwield.lib.edge        import Edge
from wordwield.db              import EdgeRecord


class ODB:
	session = None
	objects = {}

	# Class methods
	################################################################################################

	@classmethod
	def load(cls, id_or_name: int | str, o_class: 'O') -> 'O':
		if isinstance(o_class, str):
			from wordwield import ww
			o_class = ww.schemas[o_class]

		key = (o_class, id_or_name)
		if key in cls.objects:
			return cls.objects[key]

		o         = None
		orm_obj   = None
		orm_class = T(T.PYDANTIC, T.SQLALCHEMY_MODEL, o_class)

		if isinstance(id_or_name, int):
			orm_obj = cls._load_by_id(id_or_name, orm_class)
		elif isinstance(id_or_name, str):
			orm_obj = cls._load_by_name(id_or_name, orm_class)

		if orm_obj is not None:
			data     = T(T.SQLALCHEMY_MODEL, T.DATA, orm_obj)
			obj_id   = data.pop('id')
			o        = o_class.to_default()
			for k, v in data.items():
				setattr(o, k, v)

			o.__db__ = ODB(o)
			o.__id__ = obj_id

			cls.objects[key] = o
			o.db._load_edges()

		return o

	@classmethod
	def _load_by_name(cls, name: str, orm_class: 'O') -> 'O':
		orm_class.__tablename__
		orm_obj = None
		if inspect(cls.session.bind).has_table(orm_class.__tablename__):
			orm_obj = cls.session.query(orm_class).filter_by(
				name = name,
			).first()
		return orm_obj
	
	@classmethod
	def exists(cls, schema, name):
		orm_class  = T(T.PYDANTIC, T.SQLALCHEMY_MODEL, schema)
		if not inspect(cls.session.bind).has_table(orm_class.__tablename__): return False
		return bool(ODB.session.query(orm_class).filter_by(name=name).first() is not None)

	@classmethod
	def _load_by_id(cls, id, orm_class):
		return cls.session.get(orm_class, id)

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
		for other in list(ODB.objects.values()):
			if not self._o.is_o_type(other):
				continue

			for _, child in other.iter_nested():
				if child is self._o:
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
		if key in seen:
			return
		seen.add(key)

		# Заполняем все пустые single/list/dict-поля из edges
		for name, field in o.model_fields.items():
			val  = getattr(o, name, None)
			kind, _ = o.get_field_kind(name, field.annotation)
			if not val:
				setattr(o, name, self.get_related(name))

		# Рекурсивно вызываем _load_edges для всех вложенных объектов
		for _, child in o.iter_nested():
			if hasattr(child, 'db'):
				child.db._load_edges(seen)

	def _save_edges(self):
		o = self._o
		for name, field in o.model_fields.items():
			for key, child in o.iter_nested():
				val = getattr(o, name, None)
				if (
					(isinstance(val, list)  and child in val) or
					(isinstance(val, dict)  and child in val.values()) or
					(o.is_o_instance(val)   and child is val)
				):
					self._save_edge(src=o, tgt=child, rel1=name, rel2=None, key1=key, key2='')

	def _save_edge(self, src, tgt, rel1, rel2, key1='', key2=''):
		if (
			self._o.is_o_instance(tgt)
			and not getattr(tgt.db, '_is_deleted', False)
		):
			tgt.save()
			if src.id is not None:
				self.edges.set(
					id1   = src.id,
					id2   = tgt.id,
					type1 = src.__class__.__name__,
					type2 = tgt.__class__.__name__,
					rel1  = rel1,
					rel2  = rel2,
					key1  = key1,
					key2  = key2,
				)

	# Public
	################################################################################################

	@property
	def edges(self)         : return self._edge

	@property
	def table_name(self)    : return self._orm_class.__tablename__
	
	def query(self)         : return self.session.query(self._orm_class)
	def table_exists(self)  : return inspect(self.session.bind).has_table(self.table_name)
	def create_table(self)  : self._orm_class.__table__.create(bind=self.session.bind, checkfirst=True)
	def drop_table(self)    : self._orm_class.metadata.drop_all(self.session.bind)
	def filter(self, *args) : return self.query().filter(*args)
	def get(self, id)       : return self._o_or_none(self.session.get(self._orm_class, id))
	def first(self)         : return self._o_or_none(self.query().first())
	def count(self)         : return self.query().count()
	def refresh(self)       : self.session.refresh(self._o)
	def expunge(self)       : self.session.expunge(self._o)
	def add(self)           : self.session.add(self._o)
	def commit(self)        : self.create_table(); self.session.commit()
	def rollback(self)      : self.session.rollback()
	def flush(self)         : self.session.flush()
	def close(self)         : self.session.close()

	def save(self):
		data   = self._o.to_dict()
		obj_id = getattr(self._o, '__id__', None)

		data = {
			k: (None if v is PydanticUndefined else v)
			for k, v in data.items()
		}

		self.create_table()

		for _, child in self._o.iter_nested():
			child.save()

		try:
			if obj_id:
				record = self.session.get(self._orm_class, obj_id)
				if not record:
					raise ValueError(f'Record with id={obj_id} not found in table `{self._orm_class.__tablename__}`')
				for key, value in data.items():
					setattr(record, key, value)
			else:
				record = self._orm_class(**data)
				self.session.add(record)

			self.commit()

		except IntegrityError as e:
			msg = str(e).split('[')[0]
			raise RuntimeError(f'In `{self._o.__class__.__name__}`: {msg}while trying to save:\n\n{self._o}') from None

		setattr(self._o, '__id__', getattr(record, 'id', None))
		self._save_edges()
		self.commit()
		self._load_edges()
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
		if hasattr(self._o, '__id__'):
			delattr(self._o, '__id__')

	def get_related(self, name: str):
		o      = self._o
		edges  = self.edges.get(o, rel=name)
		result = []

		for edge in edges:
			if edge.rel1 == name and edge.id1 == o.id:
				result.append(ODB.load(edge.id2, edge.type2))
			elif edge.rel2 == name and edge.id2 == o.id:
				result.append(ODB.load(edge.id1, edge.type1))

		print(name)
		field = o.model_fields.get(name)
		if field is None:
			raise AttributeError(f'Field `{name}` does not exist in `{o.__class__.__name__}` schema.')
		tp = field.annotation

		if is_list(tp):
			return result or []
		if is_dict(tp):
			return {} if not result else {k: v for k, v in result}
		elif result:
			if tp == bool:
				v = result[0]
				if v in (0, '0', False, 'false', 'False', '', None):
					return False
				return True
			return tp(result[0])
		else:
			return field.default if field.default is not None else None
		
	@classmethod
	def all(cls, o_class) -> dict:
		'''
		Load all saved instances of cls (O) into a dict, key=model.name.
		'''
		orm_class = T(T.PYDANTIC, T.SQLALCHEMY_MODEL, o_class)
		if not inspect(ODB.session.bind).has_table(orm_class.__tablename__):
			return {}
		
		objects = {}
		records = ODB.session.query(orm_class).all()
		for record in records:
			data = T(T.SQLALCHEMY_MODEL, T.DATA, record)
			obj_id = data.pop('id', None)
			name = data.get('name')
			o = o_class.model_construct(**data)
			o.__db__ = ODB(o)
			o.__id__ = obj_id
			objects[name] = o
			o.db._load_edges()
		return objects
