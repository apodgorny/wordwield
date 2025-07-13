from wordwield     import ww
from wordwield.lib import O


class Character(ww.operators.Unfolder):
	agents = {
		'summarizer': ww.operators.Summarizer
	}

	@property
	async def long_memory(self):
		conversaton = self.get_conversation()
		summary = await self.agents.summarizer(conversaton.to_prompt())
	
	@property
	async def short_memory(self):
		return 'foo'
	
	def get_conversation(self):
		stream_names = [self.character.name] + self.state.peers
		return ww.schemas.StreamSchema.zip(stream_names)

	questions = [
		'Что происходит вокруг меня в данный момент? Опиши со своих глаз.',
		'Чего я хочу добиться в этой ситуации, какова моя цель в данной ситуации? (Начни с "Я хочу..")',
		'Какие воспоминания или опыт из прошлого сейчас важны для моего решения?',
		'Какое действие будет самым логичным и естественным в ответ на то, что сейчас происходит?',
	]
	template = '''
		Ты - живой персонаж {{ character.name }}

		О тебе:
		-------------------
		
		-------------------

		-------------------
		Было вот что
		{{ long_memory }}
		A потом:
		{{ short_memory }}
		И вот только что:
		-------------------

		-------------------
		{{ unfoldment }}
		-------------------

		{{question}}
		'''

	async def invoke(self, character, peers):
		return await super().invoke()
