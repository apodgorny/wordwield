import os, re, json, inspect

from jinja2 import Environment, BaseLoader

from wordwield.lib import (
	Operator,
	String,
	O,
	T
)


class Agent(Operator):
	response_schema = None
	state_schema    = None

	def __init__(self, name=None):
		self.state = None
		if self.state_schema is not None:
			self.state = self.state_schema.load(name)

	async def __call__(self, *args, **kwargs):
		self.vars = await self.get_vars()
		return await self.invoke(*args, **kwargs)
	
	######################################################################
	
	async def get_vars(self) -> dict:
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
		vars = dict(getattr(self, 'vars', {}))
		for obj in args:
			if hasattr(obj, 'to_dict'):
				vars.update(obj.to_dict())
			elif isinstance(obj, dict):
				vars.update(obj)
		vars.update(kwargs)
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
		schema                     = schema or self.response_schema
		llm_schema, non_llm_schema = schema.split('llm')
		prompt                     = prompt + '\nPut all data into JSON:\n' + llm_schema.to_schema_prompt()

		partial = await self.ww.ask(
			prompt = prompt,
			schema = llm_schema
		)
		full = schema(**{**partial, **extra_fields})
		return full.unpack()
	
	async def write(self):
		pass

	async def read(self):
		pass

	async def invoke(self, *args, **kwargs):
		read_vars = await self.read()
		self.to_vars(read_vars)
		schema = self.ww.schemas[self.state.response_type]
		prompt = self.fill(self.data.template)
		result = await self.ask(prompt=prompt, schema=schema)
		packed = schema.pack(result)
		self.to_vars(packed.to_dict())
		await self.write()