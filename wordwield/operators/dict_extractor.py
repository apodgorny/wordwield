from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class DictExtractor(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, keys, **kwargs):
		fields = {}
		schema_name = 'DictExtractorResponseSchema'

		for key in keys:
			fields[key] = O.Field(str, description=f'{self.field_description} `{key}`')

		schema = O.schema(schema_name, **fields)
		return await self.ask(self.fill(), schema=schema, unpack=False)