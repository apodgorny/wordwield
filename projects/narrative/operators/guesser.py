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
		{dialog}
		Based on previous guesses and responses guess a correct number.
	'''

	async def invoke(self, name, target_threads, source_threads):
		source = await thread_read(names=target_threads, num_beats=0)

		for beat in source:
			

		dialog = '\n'.join(dialog_lines) if dialog_lines else "No previous guesses."

		# 3. Заполняем prompt и получаем следующую попытку через LLM
		schema = GuesserSchema.load(name)
		self.to_promptlets(schema)
		prompt = self.fill(self.template, dialog=dialog)

		next_guess = await self.ask(prompt)
		await thread_write(name=guess_thread, text=str(next_guess))

		return 0
