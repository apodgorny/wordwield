from wordwield.lib import O, Operator
from wordwield import ww


class GuessingGame(ww.operators.Project):

	# Public Properties
	####################################################################################

	@property
	def history(self):
		return self.get_history()

	@property
	def has_history(self):
		return bool(self.streams.guess_stream.read())
	
	@property
	def agent_intents(self):
		return { s.name: s.schema.intent for s in self.agents if s.name != 'manager' }

	@property
	def description(self):
		return self.schema.description
	
	@property
	def guessed_number(self):
		if results := self.streams.guess_stream.read(limit=1):
			return results[0].value
		
	# Public methods
	####################################################################################

	def get_history(self, limit=None, since=None):
		history = self.ww.schemas.StreamSchema.zip([
			'guess_stream',
			'direction_stream'
		]).read(limit, since)
		with open(f'{self.ww.config.LOGS_DIR}/history.log', 'w') as f:
			f.write('\n'.join([f'{g.author} : {g.value}' for g in history]))
		return history
	
	async def invoke(self, correct_number):
		self.correct_number = correct_number
		return await super().invoke()