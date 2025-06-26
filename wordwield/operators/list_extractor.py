from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class ListExtractor(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, description, data=None):
		schema = O.schema(items = O.Field(list[str], description=description))
		self.to_state(data or {})
		return await self.ask(self.fill(), schema)