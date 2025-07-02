from wordwield.lib import O
from wordwield import ww


class Divider(ww.operators.Agent):

	class SimpleSceneSchema(O):
		title      : str = O.Field(description='Описательное название сцены')
		text       : str = O.Field(description='Точная и полная выдержка из текста которая соответствует/описывает сцену')
		# setting    : str = O.Field(description='')
		# characters : str = O.Field(description='')
		# backstory  : str = O.Field(description='')
		# outcome    : str = O.Field(description='')

	class ResponseSchema(O):
		scenes: list['Divider.SimpleSceneSchema'] = O.Field(description='Список сцен')
	

	template = '''
		Ты театральный сценарист организующий текст в сцены.
		Раздели текст на сцены.

		Текст:
		----------------------
		{{text}}
		----------------------
	'''
	
	async def invoke(self, text):
		return await self.ask()