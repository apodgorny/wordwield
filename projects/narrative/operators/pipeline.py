from wordwield.lib import O, Agent

from schemas.schemas import (
	BeatSchema,
	TimelineSchema,
	ThreadSchema
)

class Test(Agent):
	class InputType(O):
		name: str

	class OutputType(O):
		text: str

	async def invoke(self, name):
		return f'Your name is: {name}'

class Pipeline(Agent):
	class InputType(O):
		name: str

	class OutputType(O):
		text: str

	def create(self, name):
		schema = TimelineSchema(
			title   = name,
			threads = []
		).save(name)
		return schema

	@property
	async def test(self):
		return await test('fooksaw')

	async def invoke(self, name):
		schema = TimelineSchema.load(name)
		if not schema:
			schema = self.create(name)
		print(schema)
		return await self.test