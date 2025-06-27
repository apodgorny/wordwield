from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Filler(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, schema):
		self.state.filled_fields = {}
		self.state.next_field    = {}

		for name, value, field in schema.iter():
			if not value:
				self.state.next_field = {
					'name'        : name,
					'description' : field.extra['description']  # must have description set
				}
				response_schema, _ = schema.split(by=lambda n, f: n == name)
				result = await self.ask(self.fill(), schema=response_schema)
				schema[name] = result
				schema.save()
				self.state.filled_fields[name] = result
			else:
				self.state.filled_fields[name] = value