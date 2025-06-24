from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Extractor(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, data, schema):
		self.to_state(data)
		self.to_state(schema)
		return await self.ask(self.fill(), schema=schema.to_schema())