import os, re, json, inspect

from .operator  import Operator
from .string    import String
from .o         import O
from .t         import T


class Agent(Operator):

	@property
	def expertise(self) -> str | None:
		cls_name = String.camel_to_snake(self.__class__.__name__)
		for ext in ['.md', '.txt']:
			path = os.path.join(self.project['EXPERTISE_PATH'], f'{cls_name}{ext}')
			if os.path.exists(path):
				with open(path, 'r', encoding='utf-8') as f:
					return f.read()
		return None

	async def _get_vars(self) -> dict:
		props = {
			name: getattr(self, name)
			for name in dir(self.__class__)
			if isinstance(getattr(self.__class__, name), property)
		}
		result = {}
		for name, value in props.items():
			# If value is a coroutine function, await it
			if inspect.isawaitable(value):
				value = await value
			result[name] = value
		return result
	
	def to_vars(self, *args, **kwargs):
		'''
		Merge all dict-like positional arguments (schemas, dicts) and keyword arguments into self._vars.
		For O instances (or any object with .to_dict()), use .to_dict().
		'''
		base = getattr(self, '_vars', {})
		vars = dict(base)

		for obj in args:
			if hasattr(obj, 'to_dict'):
				vars.update(obj.to_dict())
			elif isinstance(obj, dict):
				vars.update(obj)

		vars.update(kwargs)
		self._vars = vars

	def fill(self, template: str, **vars) -> str:
		template = String.unindent(template)
		matches  = set(re.findall(r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}', template))
		all_vars = {**self._vars, **vars}

		for path in matches:
			if path not in all_vars:
				raise ValueError(f'[LLM] Field `{path}` mentioned in template, but not supplied')

			# Convert all pydantic/o objects in data into plain data
			value = T(T.PYDANTIC, T.DATA, all_vars[path]) # type: ignore

			if isinstance(value, (dict, list)):
				value = json.dumps(value, indent=4, ensure_ascii=False)
			else:
				value = str(value)

			template = template.replace(f'{{{{{path}}}}}', value)

		return template

	async def ask(self, prompt='', schema=None, **extra_fields):
		hr                         = '-' * 40
		schema                     = schema or self.OutputType
		llm_schema, non_llm_schema = schema.split('llm')
		prompt                     = prompt + '\nPut all data into JSON:\n' + llm_schema.to_schema_prompt()

		# self.log('INPUT', prompt, hr)
		# print('NON-LLM', json.dumps(non_llm_schema.to_schema(), indent=4))
		# print('LLM', json.dumps(llm_schema.to_schema(), indent=4))
		# print('&' * 50)

		partial = await self.globals['ask'](
			prompt         = prompt,
			response_model = llm_schema
		)
		full = schema(**{**partial, **extra_fields})
		# self.log('OUTPUT', full, hr)

		result = T(T.DATA, T.ARGUMENTS, full.to_dict())
		return result

	async def invoke_decorator(self, *args, **kwargs):
		self._vars = await self._get_vars()
		return await self.invoke(*args, **kwargs)