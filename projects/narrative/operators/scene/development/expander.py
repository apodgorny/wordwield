from wordwield.core import O
from wordwield import ww


# class SimpleSceneSchema(O):
# 	title      : str = O.Field(description='Описательное название сцены')
# 	text       : str = O.Field(description='Точная и полная выдержка из текста которая соответствует/описывает сцену')
# 	# setting    : str = O.Field(description='')
# 	# characters : str = O.Field(description='')
# 	# backstory  : str = O.Field(description='')
# 	# outcome    : str = O.Field(description='')

class Expander(ww.operators.Agent):

	class ResponseSchema(O):
		scene_text: str = O.Field(description='Beat by beat text of scene')

	template = '''
		Ты театральный сценарист прорабатывающий сцены.

		Вот общая идея книги:
		----------------------
		{{text}}
		----------------------

		{% if scenes_up_to_moment %}
			Вот, что произошло в предыдущих сценах
			Сцены:
			----------------------
			{% for scene in scenes_up_to_moment %}
				{{ scene }}
			{% endfor %}
			----------------------

			Напиши следующую сцену.
		{% else %}
			Напиши первую сцену.
		{% endif %}
		Сцена называется: "{{scene_title}}".
		Раскрой персонажи участвующие в этой сцене.
		Добавляй к уже существующему, не вноси новых персонажей, мест или событий.
	'''
	
	async def invoke(self, text, scenes_up_to_moment, scene_title):
		return await self.ask()