from wordwield.lib import Agent, O
from schemas       import PersonaSchema
from operators     import thread_read, thread_write

class Corrector(Agent):
	class InputType(O):
		name : str	                                                                     # Unique persona name (snake_case)

	class OutputType(O):
		status : int = 0	                                                             # Можно опустить, если не требуется

	async def invoke(self, name):
		persona        = PersonaSchema.load(name)
		voice_names    = [voice.name for voice in persona.voices]
		beats          = await thread_read(names=voice_names, num_beats=-1)              # Read zipped history from all voices ordered by timestamp
		consensus_text = '\n'.join(getattr(beat, 'text', str(beat)) for beat in beats)   # Stub consensus: concatenate all text from beats
		await thread_write(name=name, text=consensus_text)                               # Write consensus to persona's own thread (timestamp is set by thread_write)
		return 0
