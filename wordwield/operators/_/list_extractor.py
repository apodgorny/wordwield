from wordwield.core import O, Registry
from wordwield.operators import Agent


class ListExtractor(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, **kwargs):
		schema = O.schema(items = O.Field(list[str], description=self.field_description))
		prompt = await self.fill()
		return await self.ask(prompt, schema)