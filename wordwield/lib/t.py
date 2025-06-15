import copy, re, json
from typing import Any, get_args, get_origin, Union, List, Dict

from pydantic        import BaseModel, create_model
from pydantic.fields import FieldInfo
from sqlalchemy      import Table, Column, MetaData, Integer, String, JSON
from sqlalchemy.orm  import declarative_base

from .predicates  import is_atomic_dict, is_atomic_list, is_pydantic, is_pydantic_class, is_excluded_type, is_atomic
from .transform   import T
from .string      import String
from .record      import Record


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


@T.register(T.PYDANTIC, T.STRING)
def model_to_string(obj, base_level=0):
	tab_size = 3
	label    = f'{obj.name}:' if hasattr(obj, 'name') else ''
	id_str   = f'({label}{obj.id})' if obj.id else ''
	data     = obj.to_dict(r=False, e=True)

	def fmt_value(value, level):
		if isinstance(value, BaseModel):
			# For nested BaseModel, don't add extra indentation - it handles its own
			nested = model_to_string(value, 0)
			# Indent the entire nested string to the current level
			lines = nested.splitlines()
			indented_lines = []
			for line in lines:
				if line.strip():  # Only indent non-empty lines
					indented_lines.append(' ' * (level * tab_size) + line)
				else:
					indented_lines.append('')
			return '\n'.join(indented_lines)
		if isinstance(value, list):
			if not value:
				return '[]'
			items = []
			for v in value:
				formatted = fmt_value(v, level + 1)
				# Don't add extra indentation for BaseModel items since they handle their own
				if isinstance(v, BaseModel):
					items.append(formatted)
				else:
					items.append(' ' * ((level + 1) * tab_size) + formatted)
			return '[\n' + ',\n'.join(items) + '\n' + ' ' * (level * tab_size) + ']'
		if isinstance(value, dict):
			if not value:
				return '{}'
			items = []
			for k, v in value.items():
				formatted = fmt_value(v, level + 1)
				items.append(' ' * ((level + 1) * tab_size) + f'"{k}": {formatted}')
			return '{\n' + ',\n'.join(items) + '\n' + ' ' * (level * tab_size) + '}'
		return json.dumps(value, ensure_ascii=False)

	# Build the object representation
	base_indent = ' ' * (base_level * tab_size)
	field_indent = ' ' * ((base_level + 1) * tab_size)
	
	lines = [base_indent + f'{obj.__class__.__name__}{id_str} {{']
	
	items = list(data.items())
	for i, (k, v) in enumerate(items):
		is_last = i == len(items) - 1
		comma   = '' if is_last else ','
		formatted = fmt_value(v, base_level + 1)
		lines.append(field_indent + f'"{k}": {formatted}{comma}')
	
	lines.append(base_indent + '}')
	result = '\n'.join(lines)
	
	# Clean up extra spaces after colons
	return re.sub(':[ ]+', ': ', result)

@T.register(T.PYDANTIC, T.JSONSCHEMA)
def model_to_schema(model: type[BaseModel]) -> dict:
	return model.model_json_schema()


@T.register(T.DATA, T.TREE)
def data_to_tree(data: dict, root='', color=False):
	lines = []
	S0 = '    '
	S1 = '│   '
	S2 = '└── '
	S3 = '├── '

	def add(margin, key='', spacing='', value=None):
		lines.append({'margin': margin, 'key': key, 'spacing': spacing, 'value': value})

	def walk(node, margin='', key=None, is_last=True, key_pad=0, prev_type=None):
		connector = S2 if is_last else S3
		disp_key  = key if key is not None else ''
		if isinstance(node, dict):
			# Insert a blank line before section if previous sibling was not dict and not root
			if prev_type not in (None, dict) and (disp_key or margin):
				add(margin + (S1 if not is_last else S0))
			# Compute max key width for leaves at this level
			leaf_keys = [k for k, v in node.items() if is_atomic(v)]
			maxlen = max((len(str(k)) for k in leaf_keys), default=0)
			# Add section header line
			if disp_key or margin:
				add(margin + connector, disp_key, '', None)
			keys = list(node.keys())
			prev = None
			for i, k in enumerate(keys):
				val         = node[k]
				is_leaf     = is_atomic(val)
				last        = i == len(keys) - 1
				next_margin = margin + (S0 if is_last else S1)
				walk(val, next_margin, k, last, maxlen if is_leaf else 0, prev)
				prev = type(val)
			# Margin-aware blank line after section unless it's last
			if not is_last:
				add(margin + S1)
		elif is_atomic(node):
			pad = ' ' * (key_pad - len(str(disp_key))) if key_pad else ''
			add(margin + (S2 if is_last else S3), disp_key, pad, repr(node))
		elif isinstance(node, list):
			if disp_key or margin:
				add(margin + (S2 if is_last else S3), disp_key, '', None)
			for i, item in enumerate(node):
				last        = i == len(node) - 1
				next_margin = margin + (S0 if is_last else S1)
				walk(item, next_margin, f'[{i}]', last, prev_type=type(node))
		else:
			add(margin + (S2 if is_last else S3), disp_key, '', repr(node))

	if root:
		add('', root, '', None)
		add(S1)
		keys           = list(data.keys())
		root_leaf_keys = [k for k, v in data.items() if is_atomic(v)]
		root_key_pad   = max((len(str(k)) for k in root_leaf_keys), default=0)
		prev           = None
		for i, k in enumerate(keys):
			last    = i == len(keys) - 1
			val     = data[k]
			is_leaf = is_atomic(val)
			walk(val, '', k, last, root_key_pad if is_leaf else 0, prev)
			prev = type(val)
	else:
		walk(data, '', None, True)

	def render_line(entry):
		m, k, s, v = (entry[k] for k in ['margin','key','spacing','value'])
		if color:
			if m: m = String.color(m, String.GRAY)
			if k: k = String.color(k, String.YELLOW)
			eq = String.color(' = ', String.GRAY)
			if isinstance(v, str):
				v = re.sub(r'\(([^)]+)\)', lambda m: f'({String.color(m.group(1), String.BLUE)})', v)
		else: eq = ' = '

		if   v is not None : return f'{m}{k}{s}{eq}{v}'
		elif k             : return f'{m}{k}'

		return m  # margin-only line

	return '\n' + '\n'.join(render_line(e) for e in lines) + '\n'
