from wordwield     import ww
from wordwield.core import O


class Writer(ww.operators.Agent):
	class ResponseSchema(O):
		text: str = O.Field(description='Текст сцены')

	intent     = 'Написать драфт сцены'
	template   = '''
		Ты — писатель, который умеет писать захватывающий нарратив.
		Твоя цель — {{intent}}

		История:
		---------------------
		{{ story.time }}
		{{ story.plot }}
		---------------------

		
		{% if summary %}
			ПОСЛЕДНИЕ СОБЫТИЯ:
			---------------------
			{{ summary }}
			---------------------
		{% else %}
			Сейчас ты работаешь над первой сценой
		{% endif %}


		ТВОЁ ЗАДАНИЕ:
		Создай teхт для следующей сцены:
		---------------------
		{{ scene.to_prompt() }}
		---------------------
	'''

	async def invoke(self, story, summary, scene):
		return await self.ask()
