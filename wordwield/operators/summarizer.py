from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Summarizer(Agent):

	class ResponseSchema(O):
		summary : str = O.Field(description='Краткий но максимально полный пересказ текста от первого лица')

	template = '''
		Ты {{ name }}.
		Суммаризируй события от своего лица на РУССКОМ ЯЗЫКЕ
		-------------------
		{{ text }}
		-------------------
	'''

	# Public methods
	#########################################################################

	async def invoke(self, name, text):
		return await self.ask()