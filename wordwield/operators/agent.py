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
	ResponseSchema  : O    = None
	intent          : str  = None      # purpose, semantic role in project
	template        : str  = None      # jinja prompt template
	verbose         : bool = True

	# Magic
	######################################################################

	def __init__(self, name=None):
		super().__init__(name=name)
		Registry('state', self)
		self._register_agents()
		self._register_streams()

	async def __call__(self, *args, **kwargs):
		signature = inspect.signature(self.invoke)
		arg_names = [param.name for param in signature.parameters.values()]

		n = 0
		for n in range(min(len(args), len(arg_names))):
			kwargs[arg_names[n]] = args[n]

		args = args[n+1:]

		self.to_state(*args, **kwargs)
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

			for agent_name, agent_class in agent_dict.items():
				agent                   = agent_class(agent_name)
				agent.owner             = self
				agent.state['owner']    = self
				self.agents[agent_name] = agent

	def _register_streams(self):
		if hasattr(self.__class__, 'streams'):
			stream_list = list(self.streams)
			delattr(self.__class__, 'streams')
			Registry('streams',  self)

			for stream_name in stream_list:
				full_stream_name = f'{self.__class__.ns}.{self.name}__{stream_name}'.replace('operators.', '')
				stream = self.ww.schemas.StreamSchema.put(
					name   = full_stream_name,
					role   = stream_name,
					author = self.name
				)
				self.streams[stream_name] = stream
	
	async def _collect_props(self, state=None):
		state = state or self.state
		for name in dir(self.__class__):
			if not name.startswith('__'):
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
				raise ValueError(f'Object `{str(obj)[:20]}...` of type {type(obj)} must have associated key to be stored in state of `{self.name}`')
		self.state.update(kwargs)
	
	async def fill(self, template: str = None, **vars) -> str:
		await self._collect_props()   # Обновляем state property прямо перед шаблоном

		template = template or self.template
		if not template:
			raise RuntimeError(f'Template is not defined in `{self.name}`')
		try:
			template  = String.unindent(template)
			all_vars  = {**self.state.to_dict(), **vars, 'ww': self.ww }
			env       = Environment(loader=BaseLoader())
			env.globals = {'len' : len}
			jinja     = env.from_string(template)
			prompt    = String.unindent(jinja.render(**all_vars))
		except Exception as e:
			raise ValueError(f'Could not fill template in agent `{self.name}`: {str(e)}')
		return prompt

	async def ask(self, prompt=None, schema=None, unpack=True, verbose=None, **extra_fields):
		verbose     = self.verbose if verbose is None else verbose
		prompt      = prompt or await self.fill()
		schema      = schema or self.ResponseSchema
		instruction = f'''\n\nPut all data into JSON, output JSON ONLY. Wrap strings in quotes, make sure JSON is valid:\n'''

		if schema is None:
			raise RuntimeError(f'No ResponseSchema is defined in agent `{self.name}`')
		
		llm_schema, non_llm_schema = schema.split('llm')
		prompt                    += instruction + llm_schema.to_schema_prompt()

		print(f'\n========================[ 😎 AGENT `{self.name}` ]========================\n')

		partial = await self.ww.ask(
			prompt  = prompt,
			schema  = llm_schema,
			verbose = verbose
		)
		full = schema(**{**partial, **extra_fields})
		self.to_state(full)
		return full.unpack() if unpack else full.to_dict()

	######################################################################

	async def init(self)  : pass
	async def write(self) : pass

	async def invoke(self, *args, **kwargs):
		unpack = kwargs.pop('unpack') if 'unpack' in kwargs else True
		prompt = await self.fill(self.template)
		result = await self.ask(
			prompt  = prompt,
			schema  = self.ResponseSchema,
			unpack  = unpack,
			verbose = self.verbose
		)
		print(result, type(result))
		await self.write()
		return result
