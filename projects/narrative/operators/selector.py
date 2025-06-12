from wordwield.lib import O
from schemas       import AgentSchema

from wordwield.lib.expert import Expert


class Selector(Expert):
	class InputType(O):
		name   : str
		number : int

	class OutputType(O):
		status : int = 0

	async def invoke(self, name):
		persona = AgentSchema.load(name)
		voice(persona.voices[0].name, '')
		return self.OutputType(status=0)
