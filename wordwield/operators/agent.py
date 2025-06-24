import os, re, json, inspect

from jinja2 import Environment, BaseLoader

from wordwield.lib import (
	Registry,
	Operator,
	String,
	O
)

from wordwield.schemas.schemas import (
	AgentSchema
)


class Agent(Operator):
	response_schema = None

	# Magic
	######################################################################

	def __init__(self, name=None, schema: O = AgentSchema):
		super().__init__(name=name, schema=schema)
		Registry('state', self)

		if self.schema is not None:
			if self.schema.has_field('response_schema'):
				if self.response_schema is not None:
					self.response_schema = self.ww.schemas[self.schema.response_schema]
			self.to_state(self.schema)

	async def __call__(self, *args, **kwargs):
		self.to_state(*args, **kwargs)
		await self.init()
		await self._collect_props()
		return await self.invoke(*args, **kwargs)
	
	# Private
	######################################################################
	
	async def _collect_props(self, state=None):
		state = state or self.state
		for name in dir(self.__class__):
			if isinstance(getattr(self.__class__, name), property) and not name.startswith('__'):
				prop = getattr(self, name)
				state[name] = await prop if inspect.isawaitable(prop) else prop
	# Public
	######################################################################

	def to_state(self, *args, **kwargs):
		for obj in args:
			if O.is_o_instance(obj):
				obj = obj.to_dict()
			if isinstance(obj, dict):
				self.state.update(obj)
			else:
				# raise ValueError(f'Object `{obj}({type(obj)})` is not a dict or does not have to_dict() in agent `{self.name}`')
				...
		self.state.update(kwargs)
	
	def fill(self, template: str = None, **vars) -> str:
		template = template or self.schema.template
		try:
			template  = String.unindent(template)
			all_vars  = {**self.state.to_dict(), **vars}
			env       = Environment(loader=BaseLoader())
			jinja     = env.from_string(template)
			prompt    = String.unindent(jinja.render(**all_vars))
		except Exception as e:
			raise ValueError(f'Could not fill template in agent `{self.name}`: {str(e)}')
		return prompt

	async def ask(self, prompt='', schema=None, **extra_fields):
		schema                     = schema or self.response_schema
		llm_schema, non_llm_schema = schema.split('llm')
		prompt                    += '\n\nPut all data into JSON:\n' + llm_schema.to_schema_prompt()

		partial = await self.ww.ask(
			prompt = prompt,
			schema = llm_schema
		)
		full = schema(**{**partial, **extra_fields})
		self.to_state(full)
		return full.unpack()

	######################################################################

	async def init(self)  : pass
	async def write(self) : pass

	async def invoke(self, *args, **kwargs):
		print(f'\n========================[ AGENT `{self.name}` ]========================\n')
		print(list(self.state.keys()))
		prompt = self.fill(self.schema.template)
		result = await self.ask(prompt=prompt, schema=self.response_schema)
		await self.write()
		return result
