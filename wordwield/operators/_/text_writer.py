from wordwield.core import O, Registry
from wordwield.operators import Agent


class TextWriter(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, **kwargs):
		schema = O.schema(
			value = O.Field(str, description=self.field_description)
		)
		prompt = await self.fill()
		return await self.ask(prompt=prompt, schema=schema)