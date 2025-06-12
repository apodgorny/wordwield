import os, json, types
from typing   import Any, get_args, get_origin, Union, List, Dict

from pydantic import BaseModel, Field as PydanticField, model_validator

from .t   import T
from .odb import ODB


class O(BaseModel):

	# Magic
	############################################################################

	def __init__(self, **kwargs):
		for k in ['id', 'global_name']:
			if k in kwargs:
				raise KeyError(f'Attribute `{k}` is reserved. Use `{self.__class__.__name__}.load({k})` instead')

		super().__init__(**kwargs)
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

	@model_validator(mode="before")
	@classmethod
	def _before_validate(cls, data):
		ValidationError.last_model = cls.__name__
		return cls.on_create(data)

	@classmethod
	def on_create(cls, data):
		return data

	@classmethod
	def Field(cls, *args, description='', **kwargs):
		extra = kwargs.pop('json_schema_extra', {}) or {}
		if description:
			extra['description']  = description
			kwargs['description'] = description

		for k in list(kwargs):
			if not (isinstance(kwargs[k], type) or isinstance(kwargs[k], types.FunctionType)):
				extra[k] = kwargs[k]
			if k not in ['default', 'default_factory', 'description']:
				kwargs.pop(k)

		return PydanticField(*args, json_schema_extra=extra, **kwargs)

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
	
	@classmethod
	def split(cls, by: str):
		'''
			Splits the schema into two:
			- MySchema__True: fields where json_schema_extra[by] is True or missing
			- MySchema__False: fields where json_schema_extra[by] is explicitly False
			Returns (MySchema__True, MySchema__False)
		'''
		true_fields  = {}
		false_fields = {}
		for name, field in cls.model_fields.items():
			info         = field.json_schema_extra or {}
			flag         = info.get(by, True)
			target       = false_fields if flag is False else true_fields
			desc         = info.get('description', None)
			extras       = dict(info)
			field_kwargs = dict(description=desc, json_schema_extra=extras)
			default      = field.default if field.default is not None else ...
			target[name] = (field.annotation, default, field_kwargs)

		def make_schema(suffix, fields):
			annotations = {}
			namespace = {}

			for k, (ann, default, field_kwargs) in fields.items():
				annotations[k] = ann
				namespace[k]   = PydanticField(default, **field_kwargs)

			namespace['__annotations__'] = annotations
			return type(f'{cls.__name__}__{suffix}', (O,), namespace)

		TrueSchema  = make_schema('True',  true_fields)
		FalseSchema = make_schema('False', false_fields)
		return TrueSchema, FalseSchema
	
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

	def to_semantic_hint(self) -> str:
		data   = T(T.PYDANTIC, T.DATA, self)
		fields = self.model_fields
		lines  = []

		for name, value in data.items():
			info = fields[name].json_schema_extra or {}
			if info.get('semantic') and value is not None:
				lines.append(f'{name}: {value}')

		return ' | '.join(lines)

	def clone(self):
		data = self.to_dict()
		data.pop('id', None)
		return self.__class__(**data)

	def save(self):
		print('SAVING', self)
		self.db.save()
		return self

	def delete(self):
		self.db.delete()

	def get_description(self, field: str) -> str:
		info = self.model_fields.get(field)
		return info.description or ''
	
	def iter_nested(self):
		'''
			Yields (key, val) for all nested O-objects in single/list/dict fields (first level only).
			key:
				- None for 'single'
				- index (int) for 'list'
				- dict key for 'dict'
		'''
		for name, field in self.model_fields.items():
			kind, _ = self.get_field_kind(name, field.annotation)
			val = getattr(self, name, None)
			if kind == 'single' and val is not None:
				yield ('', val)
			elif kind == 'list' and val:
				for idx, item in enumerate(val):
					yield (str(idx), item)
			elif kind == 'dict' and val:
				for k, item in val.items():
					yield (k, item)


##################################################################################


from pydantic import ValidationError

def humanize(self):
	lines = [f'In `{ValidationError.last_model}`']
	for e in self.errors():
		var = '.'.join(str(x) for x in e.get('loc', [])) or 'unknown'
		t1  = e.get('type', 'unknown')
		v1  = e.get('input', 'unknown')
		t2  = type(v1).__name__ if v1 != 'unknown' else 'unknown'
		v1  = str(v1)
		if len(v1) > 300:
			v1 = v1[:300] + ' ...'
		if t1 == 'missing':
			line = f'  - `{var}`: is missing'
		else:
			line = f'  - `{var}`: expected `{t1}`, got `{t2}({v1})`'
		lines.append(line)
	return '\n'.join(lines)

def validationerror_str(self):
	return self.humanize()

ValidationError.humanize = humanize
ValidationError.__str__  = validationerror_str
ValidationError.__repr__ = validationerror_str
