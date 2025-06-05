import os
from typing   import Any, get_args, get_origin, Union, List, Dict

from pydantic import BaseModel, Field, model_validator

from .transform import T
from .odb       import ODB


class O(BaseModel):

	# Magic
	############################################################################

	def __init__(self, *args, **kwargs):
		for k in ['id', 'global_name']:
			if k in kwargs:
				raise KeyError(f'Attribute `{k}` is reserved. Use `{self.__class__.__name__}.load({k})` instead')

		super().__init__(*args, **kwargs)
		self.__db__ = ODB(self)

	def __getattr__(self, name: str):
		if name in self.model_fields:
			raise AttributeError(name)

		related = self.db.get_related(name)
		if not related:
			raise AttributeError(f'{self.__class__.__name__} has no attribute or edge `{name}`')
		return related

	def __str__(self) -> str:
		return T(T.PYDANTIC, T.STRING, self)

	def __repr__(self):
		return f'<{self.__class__.__name__} id={self.id}>'

	# Public class methods
	############################################################################

	@classmethod
	def Field(cls, *args, description='', semantic=False, reverse=None, **kwargs):
		extra = kwargs.setdefault('json_schema_extra', {})
		if description : extra['description'] = description
		if semantic    : extra['semantic']    = True
		if reverse     : extra['reverse']     = reverse
		return Field(*args, description=description, **kwargs)

	@classmethod
	def is_o_type(cls, tp: Any) -> bool:
		return isinstance(tp, type) and issubclass(tp, O)

	@classmethod
	def is_o_instance(cls, obj: Any) -> bool:
		return isinstance(obj, O)

	@classmethod
	def get_field_kind(cls, name, tp=None):
		tp = tp or cls.model_fields[name].annotation

		if O.is_o_type(tp):
			return 'single', tp

		if get_origin(tp) in (list, List):
			sub = get_args(tp)[0]
			if O.is_o_type(sub):
				return 'list', sub

		if get_origin(tp) in (dict, Dict):
			k, v = get_args(tp)
			if k is str and O.is_o_type(v):
				return 'dict', v

		return None, None

	@classmethod
	def to_schema_prompt(cls) -> str:
		return T(T.PYDANTIC, T.PROMPT, cls)

	@classmethod
	def to_schema(cls) -> dict:
		return T(T.PYDANTIC, T.DEREFERENCED_JSONSCHEMA, cls)

	@classmethod
	def load(cls, ref: int | str) -> 'O':
		return ODB.load(ref, cls)

	# Getters
	############################################################################

	@property
	def db(self):
		return self.__db__

	@property
	def id(self):
		return self.__dict__.get('__id__')

	# Public
	############################################################################

	def to_prompt(self)                 -> str  : return self.to_json()
	def to_json(self, r=False)          -> str  : return json.dumps(self.to_dict(r, e=True), indent=4, ensure_ascii=False)
	def to_dict(self, r=False, e=False) -> dict : return T(T.PYDANTIC, T.DATA, self, recursive=r, show_empty=e)
	def to_tree(self)                   -> str  : return T(T.PYDANTIC, T.TREE, self)
	def get_name(self)                  -> str  : return self.db.get_name()

	def to_semantic_hint(self) -> str:
		data = T(T.PYDANTIC, T.DATA, self)
		fields = self.model_fields
		lines = []

		for name, value in data.items():
			info = fields[name].json_schema_extra or {}
			if info.get('semantic') and value is not None:
				lines.append(f'{name}: {value}')

		return ' | '.join(lines)

	def clone(self):
		data = self.to_dict()
		data.pop('id', None)
		return self.__class__(**data)

	def save(self, name=None):
		self.db.save(name)
		return self

	def delete(self):
		self.db.delete()

	def get_description(self, field: str) -> str:
		info = self.model_fields.get(field)
		return info.description or ''
