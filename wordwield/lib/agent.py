import re, json

from .operator  import Operator
from .o         import O
from .string    import String
from .transform import T


class Agent(Operator):

	def _get_template(self):
		if not hasattr(self, 'template'):
			raise ValueError(f'Property `template` is not defined in `{self.__class__.__name__}`')
		return self.template

	def _get_promptlets(self) -> dict:
		return {
			name: getattr(self, name)
			for name in dir(self.__class__)
			if isinstance(getattr(self.__class__, name), property)
		}

	def fill(self, template: str, **vars) -> str:
		template = String.unindent(template)
		matches  = set(re.findall(r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}', template))
		all_vars = {**self._get_promptlets(), **vars}

		for path in matches:
			if path not in all_vars:
				raise ValueError(f'[LLM] Field `{path}` mentioned in template, but not supplied')

			# Convert all pydantic/o objects in data into plain data
			value = T(T.PYDANTIC, T.DATA, vars[path])

			if isinstance(value, (dict, list)):
				value = json.dumps(value, indent=4, ensure_ascii=False)
			else:
				value = str(value)

			template = template.replace(f'{{{{{path}}}}}', value)

		return template

	async def ask(self, prompt = None, schema = None, output_repr=True):
		hr     = '-' * 40
		schema = schema or self.OutputType
		if output_repr:
			prompt = prompt + '\nPut all data into JSON:\n' + schema.to_schema_prompt()

		self.log('INPUT', prompt, hr)

		output = await self.globals['ask'](
			prompt         = prompt,
			response_model = schema  # BaseModel
		)

		self.log('OUTPUT', output, hr)
		return output