from wordwield.lib import O, Registry
from wordwield import ww


class Project(ww.operators.Agent):
	class DefinitionSchema(O):
		name            : str
		intent          : str             # description of what project must accomplish
		description     : str             # description of the project
		manager         : str = None      # name of manager agent
		agents          : list[str]       # names of agents
		streams         : list[str]       # names of streams

	def __init__(self, name=None):
		super().__init__(name=name)
		
	async def init(self):
		...
		# Registry('streams_by_role', agent)
		# for stream_name in self.schema.streams:
		# 	stream_schema = self.ww.schemas.StreamSchema.load(stream_name)
		# 	self.streams[stream_name] = stream_schema
		# 	agent = self.agents[stream_schema.author]
		# 	agent.streams_by_role[stream_schema.role] = stream_schema

		# print('Loaded streams:', list(self.streams.keys()))
		
	async def invoke(self):
		since = 0.0
		# while True:
		# 	if prod_gulps := self.streams_by_role.prod_stream.read():
		# 		return prod_gulps
			
		# 	await self.agents.manager()

		# 	if gulps := self.streams_by_role.invoke_stream.read(since = since):
		# 		since      = gulps[0].timestamp
		# 		agent_name = gulps[0].value
		# 		await self.agents[agent_name]()
		# 	else:
		# 		break
