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
		names     : list[str]	# Names of threads (может быть 1 или много)
		num_beats : int = 1		# How many most recent beats to read; <0 for all

	class OutputType(O):
		beats : ThreadSchema    # Zipped list of all beats from all threads, sorted by timestamp

	async def invoke(self, names, num_beats=None):
		all_beats = []
		for name in names:
			thread = ThreadSchema.load(name)
			if thread and thread.beats:
				beats = thread.beats[-num_beats or None:]
				all_beats.extend(beats)

		# Sort all beats by timestamp to create a single unified “conversation” timeline
		all_beats.sort(key=lambda b: getattr(b, 'timestamp', 0))
		return ThreadSchema(beats=all_beats)

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
