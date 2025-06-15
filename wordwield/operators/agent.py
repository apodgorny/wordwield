import os, re, json, inspect

from jinja2 import Environment, BaseLoader

from wordwield.lib import (
	Operator,
	String,
	O,
	T
)


class Agent(Operator):
	async def _get_vars(self) -> dict:
		props = {
			name: getattr(self, name)
			for name in dir(self.__class__)
			if isinstance(getattr(self.__class__, name), property)
		}
		result = {}
		for name, value in props.items():
			if inspect.isawaitable(value):
				value = await value
			result[name] = value
		return result
	
	def to_vars(self, *args, **kwargs):
		base = getattr(self, 'vars', {})
		vars = dict(base)

		def check_and_update(d):
			for k, v in d.items():
				vars[k] = v

		for obj in args:
			data = obj.to_dict() if hasattr(obj, 'to_dict') else obj if isinstance(obj, dict) else {}
			check_and_update(data)

		check_and_update(kwargs)
		self.vars = vars

	def fill(self, template: str, **vars) -> str:
		try:
			template = String.unindent(template)
			all_vars = {**self.vars, **vars}
			env      = Environment(loader=BaseLoader())
			jinja    = env.from_string(template)
			prompt   = String.unindent(jinja.render(**all_vars))
		except Exception as e:
			raise ValueError(f'Could not fill template in agent `{self.name}`: {str(e)}')
		return prompt

	async def ask(self, prompt='', schema=None, **extra_fields):
		hr                         = '-' * 40
		schema                     = schema
		llm_schema, non_llm_schema = schema.split('llm')
		prompt                     = prompt + '\nPut all data into JSON:\n' + llm_schema.to_schema_prompt()

		partial = await self.ww.ask(
			prompt         = prompt,
			response_model = llm_schema
		)
		full = schema(**{**partial, **extra_fields})
		return full.unpack()

	async def __call__(self, *args, **kwargs):
		print('agent')
		self.vars = await self._get_vars()
		return await self.invoke(*args, **kwargs)
	
	async def invoke(self, *args, **kwargs):
		pass