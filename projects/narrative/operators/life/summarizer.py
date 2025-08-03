from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Summarizer(Agent):
	verbose = True

	class ResponseSchema(O):
		roles       : str = O.Field(description='От первого лица, объясни кто есть кто в диалоге, опиши роли всех участников')
		interaction : str = O.Field(description='В одно предложение охарактеризуй взаимодействие персонажей от первого лица')
		events      : str = O.Field(description='Краткий но максимально полный пересказ текста событий текста от первого лица')

	template = '''
		Ты {{ name }}.
		Суммаризируй события от своего лица на РУССКОМ ЯЗЫКЕ
		Имя говорящего персонажа написано в квадратных скобках
		-------------------
		{{ text }}
		-------------------
	'''

	# Public methods
	#########################################################################

	async def invoke(self, name, text):
		return await self.ask(unpack=False)