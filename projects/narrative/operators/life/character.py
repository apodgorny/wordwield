from wordwield     import ww
from wordwield.lib import O


class Character(ww.operators.Unfolder):
	questions = [
		'Что происходит вокруг меня в данный момент? Опиши со своих глаз.',
		'Чего я хочу добиться в этой ситуации, какова моя цель в данной ситуации? (Начни с "Я хочу..")',
		'Какое действие будет самым логичным и естественным в ответ на то, что сейчас происходит? Без вставок "от автора", без "сказал он" и пр. Только действие. 1-2 предложения.',
	]
	# 'Какие воспоминания или опыт из прошлого сейчас важны для моего решения?',
	template = '''
		Ты - живой персонаж {{ character.name }}
		О тебе:
		-------------------
		{{ character.to_prompt() }}
		-------------------
		Было вот что
		{{ summaries['long'] }}
		A потом:
		{{ summaries['short'] }}
		И вот только что:
		{{ summaries['last'] }}
		-------------------
		{{ unfoldment }}
		-------------------

		{{ question }}
		'''

	async def invoke(self, name, actors, summaries):
		self.state.character = ww.schemas.CharacterSchema.get(name)
		return await super().invoke()
