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

	async def read(self) -> dict:
		print('READING VARS:')
		vars = {}
		for var in self.data.read:
			vars[var.varname] = await stream_read(var.streams, var.length)
			print('----var', var.varname, var.streams)
			print(vars[var.varname])
		return vars

	async def write(self, result: O):
		pass