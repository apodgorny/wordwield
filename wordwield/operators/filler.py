from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Filler(Agent):

	# Public methods
	#########################################################################

	async def invoke(self, schema_name, fill_schema_class):
		self.state.filled_fields = {}
		self.state.next_field    = {}

		fill_schema = fill_schema_class.load(schema_name)

		for name, value, field in fill_schema.iter():
			if not value:
				self.state.next_field = {
					'name'        : name,
					'description' : field.extra['description']  # must have description set
				}
				response_schema, _ = fill_schema.split(by=lambda n, f: n == name)
				prompt = self.fill()
				print(response_schema)
				result = await self.ask(prompt, schema=response_schema)
				fill_schema[name] = result
				fill_schema.save()
				self.state.filled_fields[name] = result
			elif name != 'name':
				self.state.filled_fields[name] = value