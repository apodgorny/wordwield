import inspect

from jinja2 import Environment, BaseLoader

from wordwield.lib import (
	Registry,
	Operator,
	String,
	O
)

from wordwield.lib.predicates import *


class Agent(Operator):
	ResponseSchema  : O   = None
	intent          : str = None      # purpose, semantic role in project
	template        : str = None      # jinja prompt template

	# Magic
	######################################################################

	def __init__(self, name=None):
		super().__init__(name=name)
		Registry('state', self)

	async def __call__(self, *args, **kwargs):
		self.to_state(*args, **kwargs)
		self._register_agents()
		await self.init()
		await self._collect_props()
		return await self.invoke(*args, **kwargs)
	
	# Private
	######################################################################

	def _register_agents(self):
		if hasattr(self.__class__, 'agents'):
			agent_dict = dict(self.agents)
			delattr(self.__class__, 'agents')

			Registry('agents',  self)
			# Registry('streams', self)

			for agent_name, agent_class in agent_dict.items():
				agent                   = agent_class(agent_name)
				agent.owner             = self
				agent.state['owner']    = self
				self.agents[agent_name] = agent
	
	async def _collect_props(self, state=None):
		state = state or self.state
		for name in dir(self.__class__):
			if name.startswith('__'):
				prop = getattr(self.__class__, name)
				if isinstance(prop, property):
					prop = getattr(self, name)
					state[name] = await prop if inspect.isawaitable(prop) else prop
				elif is_atomic(prop):
					state[name] = prop

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
		template = template or self.template
		if not template:
			raise RuntimeError(f'Template is not defined in `{self.name}`')
		
		try:
			template  = String.unindent(template)
			all_vars  = {**self.state.to_dict(), **vars, 'ww': self.ww }
			env       = Environment(loader=BaseLoader())
			jinja     = env.from_string(template)
			prompt    = String.unindent(jinja.render(**all_vars))
		except Exception as e:
			raise ValueError(f'Could not fill template in agent `{self.name}`: {str(e)}')
		return prompt

	async def ask(self, prompt='', schema=None, unpack=True, **extra_fields):
		schema                     = schema or self.ResponseSchema
		llm_schema, non_llm_schema = schema.split('llm')
		prompt                    += '\n\nPut all data into JSON:\n' + llm_schema.to_schema_prompt()

		print(f'\n========================[ 😎 AGENT `{self.name}` ]========================\n')

		partial = await self.ww.ask(
			prompt = prompt,
			schema = llm_schema
		)
		full = schema(**{**partial, **extra_fields})
		self.to_state(full)
		return full.unpack() if unpack else full.to_dict()

	######################################################################

	async def init(self)  : pass
	async def write(self) : pass

	async def invoke(self, *args, **kwargs):
		print(list(self.state.keys()))
		prompt = self.fill(self.schema.template)
		result = await self.ask(prompt=prompt, schema=self.response_schema)
		await self.write()
		return result
