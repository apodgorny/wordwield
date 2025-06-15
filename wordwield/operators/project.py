from wordwield.lib import O, Operator

from wordwield.schemas.project import (
	ProjectSchema,
	ExpertSchema,
	StreamSchema,
	VariableSchema,
)

class Project(Operator):
	class InputType(O):
		name   : str
		number : int

	class OutputType(O):
		text: str

	def create(self, name):
		return None

	async def invoke(self, name, number):
		project = ProjectSchema.load(name) or self.create(name)
		if project:
			await stream_write('source', number)
			await expert(name=project.agents[0].name)
			result = await stream_read('target')
			return f'You guessed: {result}'
		return 'No project'
