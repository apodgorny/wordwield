from wordwield.lib import O, Operator
from schemas.schemas import (
	BeatSchema,
	ThreadSchema
)

# ThreadWrite
############################################################

class ThreadWrite(Operator):
	class InputType(O):
		name : str
		beat : BeatSchema

	class OutputType(O):
		status: int

	async def invoke(self, name, beat):
		thread = ThreadSchema.load(name)
		if not thread:
			thread = ThreadSchema(title=name, beats=[]).save(name)

		thread.beats.append(beat)
		thread.save(name)
		return 0

# ThreadRead
############################################################

class ThreadRead(Operator):
	class InputType(O):
		name     : str
		num_beats: int = 1   # How many most recent beats to read; <0 for all

	class OutputType(O):
		beats: list

	async def invoke(self, name, num_beats=1):
		thread = ThreadSchema.load(name)
		if not thread or not thread.beats:
			return []
		if num_beats < 0:
			return thread.beats
		return thread.beats[-num_beats:]

# ThreadRollback
############################################################

class ThreadRollback(Operator):
	class InputType(O):
		name     : str
		num_beats: int = 1

	class OutputType(O):
		status: int

	async def invoke(self, name, num_beats=1):
		thread = ThreadSchema.load(name)
		if not thread or not thread.beats:
			return 0

		thread.beats = thread.beats[:-num_beats]
		thread.save(name)
		return 0
