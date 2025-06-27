from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class TextWriter(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, **kwargs):
		schema = O.schema(
			value = O.Field(str, description=self.field_description)
		)
		return await self.ask(self.fill(), schema=schema)