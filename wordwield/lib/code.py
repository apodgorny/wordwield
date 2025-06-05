import inspect

from .operator import Operator
from .o        import O
from .string   import String


class Code:
	'''Encapsulates all code generation and inspection logic for operators and types.'''

	type_pool     = {}
	operator_pool = {}

	@staticmethod
	def get_code_and_schema(obj):
		try:
			code = String.unindent(inspect.getsource(obj))
		except TypeError as e:
			raise ValueError(f'Cannot get source code of `{obj.__name__}`. Ensure it is imported normally.') from e

		if issubclass(obj, Operator):
			input_type  = obj.InputType.to_schema()  if hasattr(obj, 'InputType')  else {}
			output_type = obj.OutputType.to_schema() if hasattr(obj, 'OutputType') else {}
			return {
				'name'        : String.to_snake_case(obj.__name__),
				'class_name'  : obj.__name__,
				'input_type'  : input_type,
				'output_type' : output_type,
				'code'        : code,
				'description' : inspect.getdoc(obj) or '',
				'config'      : getattr(obj, 'config', {})
			}
		else:
			raise TypeError('Unsupported object type for code and schema extraction')

	@staticmethod
	def collect_all_objects():
		import sys
		module  = sys.modules['__main__']
		objs    = {}
		visited = set()

		def recurse(mod):
			if not hasattr(mod, '__name__'):
				return
			if mod.__name__ in visited:
				return
			visited.add(mod.__name__)
			objs.update(vars(mod))
			for name in dir(mod):
				attr = getattr(mod, name, None)
				if inspect.ismodule(attr) and attr.__name__.startswith(module.__name__):
					recurse(attr)

		recurse(module)
		return objs


	@staticmethod
	def collect_operators(objects):
		Code.operator_pool = {}

		for name, obj in objects.items():
			if not inspect.isclass(obj):
				continue
			if not issubclass(obj, Operator):
				continue
			if obj is Operator:
				continue
			if name in ['Agent', 'Expert']:
				continue

			try:
				op_def = Code.get_code_and_schema(obj)
				snake  = String.to_snake_case(obj.__name__)
				Code.operator_pool[snake] = op_def
			except Exception as e:
				print(f'  ⚠️  Failed to process {name}: {e}')

		return list(Code.operator_pool.values())

	@staticmethod
	def collect_types(objects):
		Code.type_pool = {}
		seen = {}

		def collect(cls):
			name = cls.__name__
			if name in seen:
				return seen[name]

			if not inspect.isclass(cls) or not issubclass(cls, O):
				raise TypeError(f'Cannot collect non-O type: {cls}')

			entry = {
				'name'        : name,
				'class_name'  : name,
				'code'        : String.unindent(inspect.getsource(cls)),
				'description' : inspect.getdoc(cls) or ''
			}

			Code.type_pool[name] = entry
			seen[name] = entry
			return entry

		#################################

		for name, obj in objects.items():
			if inspect.isclass(obj):
				if issubclass(obj, O) and obj is not O:
					collect(obj)

		return list(Code.type_pool.values())

