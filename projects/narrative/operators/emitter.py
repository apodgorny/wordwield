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

	AgentType = AgentSchema
	ResponseType = BeatSchema

	template = '''
		{history}
		Based on previous guesses and responses guess a correct number.
	'''

	# async def invoke(self, name):
	# 	agent = AgentSchema.load(name)
	# 	source = await stream_read(names=agent.type, num_beats=0)

	# 	history  = []
	# 	for beat in source:
	# 		history.append(beat.to_prompt())
	# 	history = '\n'.join(history)
	# 	print('History:', history)

	# 	prompt = self.fill(self.template, history=history)
	# 	next_guess = await self.ask(prompt, schema=BeatSchema)
	# 	await stream_write(name=target_threads, text=str(next_guess))

	# 	return 0
