from wordwield.lib import O, Operator
from schemas.schemas import (
	BeatSchema,
	StreamSchema,
	AgentSchema
)

# StreamWrite
############################################################

class StreamWrite(Operator):
	class InputType(O):
		names  : list[str]       # Names of threads (one or many)
		beat   : BeatSchema

	class OutputType(O):
		status : int

	async def invoke(self, names, beat):
		if isinstance(names, str):
			names = [names]

		for name in names:
			stream = StreamSchema.load(name)
			if not stream:
				print('namess', name)
				stream = StreamSchema(name=name, beats=[]).save(name)
			stream.beats.append(beat)
			print('Saving stream', name, flush=True)
			stream.save(name)
			if stream.triggers:
				agent = AgentSchema.load(stream.triggers)
				await self.call(agent.type, name=agent.name)
		return 0


