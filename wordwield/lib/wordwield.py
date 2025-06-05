import os, sys, inspect, httpx, ast, json

from pathlib  import Path
from pydantic import BaseModel

from .string      import String
from .highlight   import Highlight
from .operator    import Operator
from .code        import Code

DAPI_URL = os.path.join(os.environ.get('DAPI_URL'))
os.environ['CLIENT'] = __file__


class WordWield:
	verbose        = False
	is_initialized = False

	# Private methods
	############################################################################

	@staticmethod
	def _create_type(type_dict):
		res = WordWield.request('POST', '/create_type', json=type_dict)
		WordWield.success(f'Type `{type_dict["name"]}` created')
		return res

	@staticmethod
	def _create_operator(operator_dict):
		res = WordWield.request('POST', '/create_operator', json=operator_dict)
		WordWield.success(f'Operator `{operator_dict["name"]}` created')
		return res

	@staticmethod
	def _color(severity):
		return {
			'fyi'    : String.LIGHTBLUE,
			'beware' : String.LIGHTYELLOW,
			'halt'   : String.LIGHTRED,
			'success': String.LIGHTGREEN
		}.get(severity, '')

	@staticmethod
	def _extract_dapi_error(response: httpx.Response):
		data = response.json()
		try:
			detail      = data.get('detail', {})
			severity    = detail.get('severity', 'halt')
			message_raw = detail.get('detail', 'Unknown error')
			trace       = detail.get('trace')

			try:
				parsed = ast.literal_eval(message_raw)
				if isinstance(parsed, dict) and 'detail' in parsed:
					message = parsed['detail']
				else:
					message = message_raw
			except Exception:
				message = message_raw

			error_type = detail.get('error_type')
			operator   = detail.get('operator')
			lineno     = detail.get('line')
			filename   = detail.get('file')
			short_file = Path(filename).name if filename else None

			parts = []
			if error_type : parts.append(error_type)
			if operator   : parts.append(f'operator: {operator}')
			if lineno     : parts.append(f'line: {lineno}')
			if short_file : parts.append(f'file: {short_file}')

			if parts:
				message += f' ({", ".join(parts)})'

			return severity, message, trace

		except Exception as e:
			return 'halt', f'Could not parse DAPI error: {e}\nOriginal error: {json.dumps(data, indent=4)}', None

	# Public methods
	############################################################################

	@classmethod
	def init(cls):
		print('init')
		'''Create all Operator and O-descendant types defined in the caller scope.'''
		# frame     = inspect.currentframe().f_back.f_back
		# module    = inspect.getmodule(frame)
		# objects   = vars(sys.modules[module.__name__])
		objects   = Code.collect_all_objects()
		operators = Code.collect_operators(objects)
		Code.collect_types(objects)  # populates type_pool including nested

		for type_def in Code.type_pool.values():  # includes all, not just roots
			WordWield._create_type(type_def)

		for op_def in operators:
			print(op_def)
			WordWield._create_operator(op_def)

		cls.is_initialized = True

	@staticmethod
	def print(*args, **kwargs):
		kwargs['flush'] = True
		color = kwargs.pop('color', None)
		if color:
			args = [String.color(arg, color) for arg in args]
		print(*args, **kwargs)

	@staticmethod
	def success(message):
		if WordWield.verbose:
			prefix = String.color('SUCCESS:', String.LIGHTGREEN)
			WordWield.print(f'{prefix} {message}')

	@staticmethod
	def error(severity, message, info=None, trace=None):
		prefix = String.color(severity.upper() + ':', WordWield._color(severity))
		message = str(message).replace('\n', '\n')
		WordWield.print(f'{prefix} {message}')
		if info is not None:
			WordWield.print(String.color(info, String.GRAY))
		if trace is not None:
			WordWield.print(String.color(trace, String.GRAY))
		exit(0)

	@staticmethod
	def request(method: str, path: str, **kwargs):
		url_name = kwargs.get('json', {}).get('name', '')
		url      = '/'.join([DAPI_URL, path.lstrip('/'), url_name]).strip('/')
		kwargs.setdefault('timeout', 1200.0)

		if WordWield.verbose:
			bar = f'  {"- " * 22}'
			WordWield.print('\n' + ('-' * 45))
			if 'json' in kwargs:
				for key, val in kwargs['json'].items():
					if isinstance(val, dict):
						val = json.dumps(val, indent=2, ensure_ascii=False)
						val = Highlight.python(val)
						WordWield.print()
						for line in val.splitlines():
							WordWield.print(f'    {line}')
					else:
						val = Highlight.python(str(val))
						WordWield.print(val)
				WordWield.print(bar, color=String.DARK_GRAY)

		try:
			res  = httpx.request(method, url, **kwargs)
			data = res.json()

			if res.status_code >= 400:
				severity = data.get('severity', 'halt')
				detail   = data.get('detail', f'Status {res.status_code}')
				file     = data.get('file')
				line     = data.get('line')
				operator = data.get('operator')
				trace    = data.get('trace')

				info  = ''
				parts = []

				if operator : parts.append(f'operator: {operator}')
				if file     : parts.append(f'file: {Path(file).name}')
				if line     : parts.append(f'line: {line}')
				if parts    : info = ', '.join(parts)

				WordWield.error(severity, f'DAPI Error: {detail}', info, trace)
			return data

		except Exception as e:
			WordWield.error('halt', str(e))
			raise

	@classmethod
	def invoke(cls, operator: Operator, *args, **kwargs):
		if not cls.is_initialized:
			cls.init()

		name = String.camel_to_snake(operator.__name__)

		if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
			input_data = args[0]
		else:
			input_data = kwargs

		# ✅ Recursively convert all O models to dicts
		def to_json_safe(obj):
			if hasattr(obj, 'to_dict'):
				return obj.to_dict()
			if isinstance(obj, dict):
				return {k: to_json_safe(v) for k, v in obj.items()}
			if isinstance(obj, list):
				return [to_json_safe(i) for i in obj]
			return obj

		input_data = to_json_safe(input_data)

		# 🧠 Validate OutputType presence
		if not hasattr(operator, 'OutputType'):
			raise TypeError(f'Operator {operator.__name__} must define OutputType')

		OutputType = operator.OutputType

		if not issubclass(OutputType, BaseModel):
			raise TypeError(f'OutputType of {operator.__name__} must be subclass of `BaseModel`')

		# 🌐 Request and parse response
		result_dict = cls.request('POST', f'{name}', json=input_data)['output']

		# 📎 Show result
		cls.success(f'Invoked operator `{name}`:\n')
		cls.print(Highlight.python(json.dumps(result_dict, ensure_ascii=False, indent=4)))

		# 📦 Convert to model
		output_model = OutputType.model_validate(result_dict)

		# 🎯 Unpack
		fields = list(OutputType.model_fields)
		if len(fields) == 1:
			return getattr(output_model, fields[0])
		else:
			return tuple(getattr(output_model, f) for f in fields)
