from wordwield.lib import O, Agent, Operator

from schemas.schemas import (
	TimelineSchema,
	PersonaSchema
)

class Timeline(Operator):
	class InputType(O):
		name: str

	class OutputType(O):
		text: str

	def create(self, name):
		timeline = TimelineSchema(
			personas = [
				PersonaSchema(
					name  = 'guesser',
					agent = 'Guesser'
				),
				PersonaSchema(
					name  = 'corrector',
					agent = 'Corrector'
				)
			]
		).save(name)
		return timeline

	async def invoke(self, name):
		timeline = TimelineSchema.load(name) or self.create(name)
		timeline = TimelineSchema.load(name)
		print(timeline)
		return 'asdf'
