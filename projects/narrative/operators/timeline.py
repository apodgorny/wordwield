from wordwield.lib import O, Agent, Operator

from schemas.schemas import (
	TimelineSchema,
)

class Timeline(Operator):
	class InputType(O):
		name: str

	class OutputType(O):
		text: str

	def create(self, name):
		timeline = TimelineSchema(
			title   = name,
			threads = []
		).save(name)
		return timeline

	async def invoke(self, name):
		timeline = TimelineSchema.load(name)
		if not timeline:
			timeline = self.create(name)
		print(timeline)
		return 'asdf'
