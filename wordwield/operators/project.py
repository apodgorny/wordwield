from wordwield.lib import O, Registry
from wordwield import ww


class Project(ww.operators.Agent):
	def __init__(self, name=None, schema: O = ww.schemas.ProjectSchema):
		super().__init__(name=name, schema=schema)
		Registry('agents',  self)
		Registry('streams', self)
		Registry('streams_by_role', self)

	async def init(self):
		for agent_name in self.schema.agents:
			agent_schema            = self.ww.schemas.AgentSchema.load(agent_name)
			agent                   = agent_schema.to_operator()
			agent.project           = self
			agent.state['project']  = self
			self.agents[agent_name] = agent

		for stream_name in self.schema.streams:
			stream_schema = self.ww.schemas.StreamSchema.load(stream_name)
			self.streams[stream_name]                = stream_schema
			self.streams_by_role[stream_schema.role] = stream_schema

		print('Loaded streams:', list(self.streams.keys()))
		
	async def invoke(self):
		since = 0.0
		while True:
			if prod_gulps := self.streams_by_role.prod_stream.read():
				return prod_gulps
			
			await self.agents.manager()

			if gulps := self.streams_by_role.invoke_stream.read(since = since):
				since      = gulps[0].timestamp
				agent_name = gulps[0].value
				await self.agents[agent_name]()
			else:
				break
