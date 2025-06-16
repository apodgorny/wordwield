from wordwield.lib import O
from wordwield import ww

from wordwield.schemas.project import (
	ProjectSchema,
	ExpertSchema,
	StreamSchema,
	VariableSchema,
)

class Project(ww.operators.Agent):
	def __init__(self, name):
		self.vars = {}

	async def invoke(self, name, number):
		project = ProjectSchema.load(name) or self.create(name)
		if project:
			await stream_write('source', number)
			await expert(name=project.agents[0].name)
			result = await stream_read('target')
			return f'You guessed: {result}'
		return 'No project'
