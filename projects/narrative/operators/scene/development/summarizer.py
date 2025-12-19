from wordwield     import ww
from wordwield.core import O


class Summarizer(ww.operators.Agent):
	class ResponseSchema(O):
		text: str

	intent     = 'Сжато суммаризировать все сцены в один-два абзаца текст'
	template   = '''
		Ты — суммаризатор, который умеет уместить предыдущие сцены в информативный сжатый блок.
		Твоя цель — {{intent}}

		Все сцены истории:
		{% for scene in scenes %}
			{{ scene }}
		{% endfor %}

		ТВОЁ ЗАДАНИЕ:
		Суммаризируй в один-два абзаца.
	'''

	async def invoke(self, scenes):
		return await self.ask()
