from wordwield.lib import Agent, O
from schemas       import GuesserSchema
from operators     import thread_read, thread_write

class Guesser(Agent):
	class InputType(O):
		name           : str  # Unique guesser name (snake_case)
		target_threads : list[str]
		source_threads : list[str]

	class OutputType(O):
		status : int = 0

	Schema = GuesserSchema

	template = '''
		{history}
		Based on previous guesses and responses guess a correct number.
	'''

	async def invoke(self, name, target_threads, source_threads):
		source = await thread_read(names=source_threads, num_beats=0)

		history  = []
		for beat in source:
			history.append(beat.to_prompt())
		history = '\n'.join(history)

		schema = GuesserSchema.load(name)
		self.to_promptlets(schema, history=history)
		prompt = self.fill(self.template)

		next_guess = await self.ask(prompt, persona='Guesser', voice='Guesser')
		await thread_write(name=target_threads, text=str(next_guess))

		return 0
