import copy, re, json
from typing import Any, get_args, get_origin, Union, List, Dict

from pydantic        import BaseModel, create_model
from pydantic.fields import FieldInfo
from sqlalchemy      import Table, Column, MetaData, Integer, String
from sqlalchemy.orm  import declarative_base

from .t import T
from .record import Record


T.PYDANTIC(BaseModel)
T.JSONSCHEMA(dict)
T.DEREFERENCED_JSONSCHEMA(dict)
T.DATA()
T.ARGUMENTS(None)
T.SQLALCHEMY_MODEL(object)
T.PROMPT(str)
T.FIELD(FieldInfo)
T.TYPE(str)
T.STRING(str)
T.TREE(dict)

class PYDANTIC:
	@staticmethod
	def is_pydantic(value):
			return isinstance(value, BaseModel)

	@staticmethod
	def is_pydantic_class(tp):
		return isinstance(tp, type) and issubclass(tp, BaseModel)

	@staticmethod
	def is_excluded_type(tp):
		# unwrap Optional[...] → T
		if get_origin(tp) is Union:
			args = [a for a in get_args(tp) if a is not type(None)]
			if len(args) == 1:
				tp = args[0]

		origin = get_origin(tp)
		args   = get_args(tp)

		if PYDANTIC.is_pydantic_class(tp) : return True
		if origin in (list, List)         : return len(args) == 1                    and PYDANTIC.is_pydantic_class(args[0])
		if origin in (dict, Dict)         : return len(args) == 2 and args[0] is str and PYDANTIC.is_pydantic_class(args[1])

		return False

@T.register(T.PYDANTIC, T.STRING)
def model_to_string(obj):
	name   = obj.db.get_name()
	label  = f'{name}:' if name else ''
	id_str = f'({label}{obj.id})' if obj.id else ''
	data   = obj.to_dict(r=False, e=True)

	def indent(text, level):
		pad = ' ' * (level * 4)
		return '\n'.join(pad + line if line else '' for line in text.splitlines())

	def fmt_value(value, level=1):
		if isinstance(value, BaseModel):
			return indent(str(value), level)
		if isinstance(value, list):
			if value:
				items = ',\n'.join(fmt_value(v, level + 1) for v in value)
				return '[\n' + items + '\n' + ' ' * (level * 4) + ']'
			return '[]'
		if isinstance(value, dict):
			if value:
				items = ',\n'.join(
					' ' * ((level + 1) * 4) + f'"{k}": {fmt_value(v, level + 1)}'
					for k, v in value.items()
				)
				return '{\n' + items + '\n' + ' ' * (level * 4) + '}'
			return '{}'
		return json.dumps(value, ensure_ascii=False)

	lines = [f'{obj.__class__.__name__}{id_str} {{']

	items = list(data.items())
	for i, (name, value) in enumerate(items):
		is_last = i == len(items) - 1
		comma   = '' if is_last else ','
		lines.append(f'    "{name}": {fmt_value(value, 1)}{comma}')
		
	lines.append('}')
	return re.sub(':[ ]+', ': ', '\n'.join(lines))


@T.register(T.PYDANTIC, T.JSONSCHEMA)
def model_to_schema(model: type[BaseModel]) -> dict:
	return model.model_json_schema()


@T.register(T.PYDANTIC, T.DATA)
def model_to_data(obj, recursive=False, show_empty=False):
	def convert(value, seen):
		if PYDANTIC.is_pydantic(value):
			if recursive:
				if id(value) in seen:
					return None
				seen.add(id(value))
				return {
					k: convert(v, seen)
					for k, v in value.model_dump().items()
				}
			else:
				return None

		if isinstance(value, dict):
			return {
				k: convert(v, seen)
				for k, v in value.items()
				if recursive or not PYDANTIC.is_pydantic(v)
			}

		if isinstance(value, (list, tuple, set)):
			return [
				convert(v, seen)
				for v in value
				if recursive or not PYDANTIC.is_pydantic(v)
			]

		return value

	if PYDANTIC.is_pydantic(obj):
		if not recursive:
			return {
				k: getattr(obj, k)
				for k, f in obj.model_fields.items()
				if show_empty or not PYDANTIC.is_excluded_type(f.annotation)
			}
		return convert(obj, seen=set())

	return convert(obj, seen=set())


@T.register(T.JSONSCHEMA, T.DEREFERENCED_JSONSCHEMA)
def dereference_schema(schema: dict) -> dict:
	def resolve_refs(obj, defs):
		if isinstance(obj, dict):
			if '$ref' in obj:
				ref_name = obj['$ref'].split('/')[-1]
				
				# Try from $defs
				if ref_name in defs:
					return resolve_refs(defs[ref_name], defs)

				# Try from globals (must be a Pydantic model)
				if ref_name in globals():
					ref_cls = globals()[ref_name]
					if hasattr(ref_cls, 'model_json_schema'):
						return resolve_refs(ref_cls.model_json_schema(), defs)

				# Fallback: raise error
				raise TypeError(f'Referenced type `{ref_name}` not found in $defs or globals()')

			return {k: resolve_refs(v, defs) for k, v in obj.items()}

		elif isinstance(obj, list):
			return [resolve_refs(item, defs) for item in obj]

		else:
			return obj

	copied = copy.deepcopy(schema)
	defs   = copied.pop('$defs', {})
	return resolve_refs(copied, defs)
	

@T.register(T.DATA, T.ARGUMENTS)
def data_to_arguments(data):
	if isinstance(data, list):
		return data
	elif isinstance(data, dict):
		args = tuple(data[k] for k in data)
		if len(args) == 1:
			args = args[0]
	return args


######################################## SQLALCHEMY ########################################


@T.register(T.PYDANTIC, T.SQLALCHEMY_MODEL)
def pydantic_to_sqlalchemy_model(model: type[BaseModel]) -> type:
	fields = {}

	if issubclass(model, BaseModel):
		fields['id'] = Column(Integer, primary_key=True, autoincrement=True)

		for name, field in model.model_fields.items():
			is_id_field = name == 'id'                            # Skip 'id' — already handled
			ftype       = field.annotation                        # Raw field type
			excluded    = PYDANTIC.is_excluded_type(ftype)        # Nested Pydantic models are stored via edges

			if not is_id_field and not excluded:
				sql_type = (                                       # Map basic types to SQLAlchemy columns
					Integer if ftype is int  else
					String  if ftype is str  else
					JSON    if ftype is dict else
					String
				)

				nullable     = not field.is_required()            # Optional fields become nullable
				fields[name] = Column(sql_type, nullable=nullable)

		name  = model.__name__ + 'Orm'
		table = type(name, (Record,), {
			'__tablename__'  : model.__name__.lower(),
			'__table_args__' : {
				'extend_existing'      : True,
				'sqlite_autoincrement' : True
			},
			**fields
		})

	else:
		table = model  # Already a table — passthrough

	return table


@T.register(T.SQLALCHEMY_MODEL, T.PYDANTIC)
def sqlalchemy_model_to_pydantic(orm_cls: type) -> type[BaseModel]:
	fields = {}

	for col in orm_cls.__table__.columns:
		if   isinstance(col.type, Integer) : py_type = int
		elif isinstance(col.type, String)  : py_type = str
		else                               : py_type = str  # fallback

		required = col.nullable is False and col.default is None and not col.autoincrement
		default  = ... if required else None

		fields[col.name] = (py_type, default)

	name = orm_cls.__name__.replace('Orm', '') + 'Schema'
	return create_model(name, **fields)


@T.register(T.SQLALCHEMY_MODEL, T.DATA)
def sqlalchemy_model_to_data(obj):
	if not hasattr(obj, '__table__'):
		raise TypeError(f'❌ Expected SQLAlchemy model, got: {type(obj)} → {obj}')
	columns = set(obj.__table__.columns.keys())
	return {
		k: getattr(obj, k)
		for k in columns
	}


######################################## TYPE ########################################

@T.register(T.TYPE, T.STRING)
def type_to_string(tp: Any) -> str:
	origin = get_origin(tp)
	args   = get_args(tp)

	if origin is Union and type(None) in args:
		non_none = [a for a in args if a is not type(None)]
		return T(T.TYPE, T.STRING, non_none[0])

	if origin in (list, List):
		item_type = args[0] if args else Any
		item_str  = T(T.TYPE, T.STRING, item_type)
		return f'List[{item_str}]'

	if origin in (dict, Dict):
		key_type   = args[0] if args else Any
		value_type = args[1] if len(args) > 1 else Any
		key_str    = T(T.TYPE, T.STRING, key_type)
		val_str    = T(T.TYPE, T.STRING, value_type)
		return f'Dict[{key_str}, {val_str}]'

	if hasattr(tp, '__name__'):
		return tp.__name__

	return str(tp)

@T.register(T.TYPE, T.PROMPT)
def type_to_prompt(tp: Any, indent: int = 0) -> str:
	origin = get_origin(tp)
	args   = get_args(tp)

	# Optional[X]
	if origin is Union and type(None) in args:
		non_none = [a for a in args if a is not type(None)]
		return T(T.TYPE, T.PROMPT, non_none[0], indent)

	# List[T] (with recursive support)
	if origin in (list, List):
		item_type = args[0] if args else Any
		if hasattr(item_type, 'model_fields'):
			body   = T(T.TYPE, T.PROMPT, item_type, indent + 1)
			pad    = '  ' * (indent + 1)
			lines  = body.splitlines()
			indented = '\n'.join(pad + line for line in lines)
			return '[\n' + indented + '\n' + '  ' * indent + ', ... ]'
		else:
			type_str = T(T.TYPE, T.STRING, item_type)
			return f'[ {type_str} ]'

	# Dict[...] (fallback only)
	if origin in (dict, Dict):
		key_type   = args[0] if args else Any
		value_type = args[1] if len(args) > 1 else Any
		key_name   = T(T.TYPE, T.STRING, key_type)
		val_str    = T(T.TYPE, T.PROMPT, value_type, indent + 1)
		return f'{{ "{key_name}": {val_str} }}'

	# Submodel
	if hasattr(tp, 'model_fields'):
		return T(T.PYDANTIC, T.PROMPT, tp, indent)

	return T(T.TYPE, T.STRING, tp)


@T.register(T.FIELD, T.PROMPT)
def field_to_prompt(field: FieldInfo, indent: int = 0) -> str:
	comment = f'  # {field.description}' if field.description else ''
	value   = T(T.TYPE, T.PROMPT, field.annotation, indent + 1)
	pad     = '  ' * indent
	return f'{pad}"{field.title}": {value}{comment}'


@T.register(T.PYDANTIC, T.PROMPT)
def pydantic_to_prompt(model_cls: type[BaseModel], indent: int = 0) -> str:
	lines = []
	pad = '  ' * indent
	lines.append(pad + '{')
	for name, field in model_cls.model_fields.items():
		field.title = name
		lines.append(T(T.FIELD, T.PROMPT, field, indent + 1))
	lines.append(pad + '}')
	return '\n'.join(lines)


@T.register(T.DATA, T.TREE)
def data_to_tree(data: dict, prefix=''):
	def walk(node, prefix='', is_last=True):
		conn    = '└── ' if is_last else '├── '
		subpref = '    ' if is_last else '│   '

		if isinstance(node, dict):
			keys = list(node.keys())
			for i, k in enumerate(keys):
				is_last = i == len(keys) - 1
				val = node[k]
				print(f'{prefix}{conn}{k}')
				walk(val, prefix + subpref, is_last)
		elif isinstance(node, list):
			for i, item in enumerate(node):
				is_last = i == len(node) - 1
				print(f'{prefix}{"└── " if is_last else "├── "}[{i}]')
				walk(item, prefix + ('    ' if is_last else '│   '), is_last)
		else:
			print(f'{prefix}{conn}{repr(node)}')

	walk(data)

