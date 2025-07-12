from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Summarizer(Agent):

	class ResponseSchema(O):
		summary    : str = O.Field(description='Краткий но максимально полный пересказ текста')
		last_event : str = O.Field(description='Краткий пересказ последнего события в тексте. 1-2 предложения.')

	template = '''
		Ты писатель.
		Суммаризируй текст и опиши последнее событие произошедьшее в тексте.
		ТЕКСТ:
		-------------------
		{{text}}
		-------------------
		Суммаризируй на РУССКОМ ЯЗЫКЕ
	'''

	# Public methods
	#########################################################################

	async def invoke(self, text):
		return await self.ask()