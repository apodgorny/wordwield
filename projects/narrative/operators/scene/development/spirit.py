from wordwield     import ww
from wordwield.lib import O


class Spirit(ww.operators.Agent):
	class ResponseSchema(O):
		plot: str = O.Field(description='План внешнего воздействия обстоятельствами, неизбежно приводящий к итогу сцены: 1-3 предложения.')

	intent     = 'разработать план внешних для персонажа событий, которые приведут к итогу сцены'
	template   = '''
		Ты — писатель, который создаёт не зависящие от персонажей обстоятельства для сцены.
		Твоя цель — {{intent}}

		Общая идея истории:
		-----------------------
		{{ story.to_prompt() }}
		-----------------------

		{% if scenes %}
			Все сцены истории:
			{% for scene in scenes %}
				- {{ scene.name }}: {{ scene.description }}
			{% endfor %}
		{% endif %}

		ТВОЁ ЗАДАНИЕ:
		Ты продумываешь сцену "{{ current_scene.name }}: {{ current_scene.description }}"
		Персонажи, которые участвуют в этой сцене {{ current_scene.characters }}
		Придумай цепь обстоятельств, которые неизбежно приведут
		к итогу сцены: "{{ current_scene.outcome }}". Пусть события соответствуют идее истории и жанру "{{ story.genre }}"
		Пиши схематично как сценарий - без эпитетов и лишних событий.
	'''

	async def invoke(self, story, scenes, current_scene):
		return await self.ask()
