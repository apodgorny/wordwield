from wordwield.lib import Agent, O
from schemas       import VoiceSchema
from operators     import ThreadWrite

class Voice(Agent):
	class InputType(O):
		name    : str                                        # Unique voice name (persona__voice, snake_case)
		history : str                                        # Preformatted history string from Persona

	class OutputType(O):
		status : int = 0	                                 # You can omit this if your framework allows empty output

	async def invoke(self, name, history):
		voice = VoiceSchema.load(name)                       # Load voice config and prompt template from schema
		self.to_promptlets(voice)
		prompt   = self.fill(voice.prompt, history=history)  # Fill prompt with loaded promptlets and history
		response = await self.ask(prompt)                    # Generate reply using LLM
		await ThreadWrite.invoke(name=name, text=response)   # Write response to thread (timestamp handled by ThreadWrite)
		return 0	                                         # Or simply `return` if output can be empty
