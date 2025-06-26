from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class DictExtractor(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, keys, description, data=None):
		fields = {}
		schema_name = 'DictExtractorResponseSchema'

		for key in keys:
			fields[key] = O.Field(str, description=f'{description} `{key}`')

		schema = O.schema(schema_name, **fields)
		self.to_state(data or {})
		self.state.keys = keys
		return await self.ask(self.fill(), schema=schema, unpack=False)