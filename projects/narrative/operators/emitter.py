from wordwield.lib import O, Expert

from schemas.schemas import (
	AgentSchema,
	StreamSchema,
	BeatSchema
)

class Emitter(Expert):
	class InputType(O):
		name : str

	class OutputType(O):
		status : int = 0

	AgentType    = AgentSchema
	ResponseType = BeatSchema

	async def read(self, agent) -> dict:
		print('READING VARS:')
		for var in agent.read:
			print('----var', var.varname)

	async def write(self, result: O):
		pass