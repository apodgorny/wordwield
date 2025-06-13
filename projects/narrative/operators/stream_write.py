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
			print(name)
			stream = StreamSchema.load(name)
			if stream is None:
				print('namess', name)
				stream = StreamSchema(name=name, beats=[])
			stream.beats.append(beat)
			stream.save()
			if stream.triggers:
				agent = AgentSchema.load(stream.triggers)
				await self.call(agent.type, name=agent.name)
		return 0


