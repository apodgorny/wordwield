from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Unfolder(Agent):

	# Public methods
	#########################################################################

	async def invoke(self):
		if not hasattr(self, 'questions') or not isinstance(self.questions, list):
			raise RuntimeError(f'Undefined attribute self.questions in unfolder agent `{self.name}`')
		
		schema = O.schema(
			answer = O.Field(str, description='your response')
		)

		answer                = ''
		unfoldment            = {}
		self.state.question   = ''
		self.state.unfoldment = ''

		for question in self.questions:
			self.state.question = question
			prompt = await self.fill()
			answer = await self.ask(prompt=prompt, schema=schema)
			unfoldment[question] = answer
			self.state.unfoldment = '\n'.join(unfoldment.values())
		return answer