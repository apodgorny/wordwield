from wordwield     import ww
from wordwield.core import O


class Extractor(ww.operators.ListExtractor):
	intent            = 'Екстрагировать из текста описание характеризующее персонажа'
	field_description = 'Описания из текста характеризуюие персонажа'
	template          = '''
		Ты — писатель, который организует персонажей из текста.
		Твоя цель — {{intent}}

		Имя персонажа: {{character_name}}

		Текст:
		-----------
		{{text}}
		-----------
		
		Выдели из текста отрывки характеризующие или описывающие персонажа {{character_name}}.
		На основе каждого отрывка дай короткую (3-7 слов) характеристику особенности персонажа, психологию, внешний вид, род занятий, пол, возраст.
	'''

	async def invoke(self, character_name, text):
		return await super().invoke()