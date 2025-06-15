from wordwield.lib import O, Operator
from wordwield.schemas.project import (
	BeatSchema,
	StreamSchema,
	ExpertSchema
)

# StreamWrite
############################################################

class StreamWrite(Operator):
	class InputType(O):
		names  : list[str]       # Names of streams (one or many)
		text   : str

	class OutputType(O):
		status : int

	async def invoke(self, names, text):
		if isinstance(names, str):
			names = [names]

		beat = BeatSchema(text=str(text))

		for name in names:
			stream = StreamSchema.load(name)
			if stream is None:
				stream = StreamSchema(name=name, beats=[])
			stream.beats.append(beat)
			stream.save()
			print(f'STREAM: `{text}` => `{name}`')
			if stream.triggers:
				agent = ExpertSchema.load(stream.triggers)
				if agent is None:
					raise KeyError(f'Could not delegate task. Agent `{stream.triggers}` is not found')
				await self.call(agent.type, name=agent.name)
		return 0


