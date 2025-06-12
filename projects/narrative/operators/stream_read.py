from wordwield.lib import O, Operator
from schemas.schemas import (
	StreamSchema,
)

# StreamRead
############################################################

class StreamRead(Operator):
	class InputType(O):
		names     : list[str]	# Names of threads (может быть 1 или много)
		num_beats : int = 1		# How many most recent beats to read; <0 for all

	class OutputType(O):
		beats : StreamSchema    # Zipped list of all beats from all threads, sorted by timestamp

	async def invoke(self, names, num_beats=None):
		all_beats = []
		for name in names:
			thread = StreamSchema.load(name)
			if thread and thread.beats:
				beats = thread.beats[-num_beats or None:]
				all_beats.extend(beats)

		# Sort all beats by timestamp to create a single unified “conversation” timeline
		all_beats.sort(key=lambda b: b.timestamp)
		return 'asdf'#StreamSchema(name='+'.join(names), beats=all_beats)
	