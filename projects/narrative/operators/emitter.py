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