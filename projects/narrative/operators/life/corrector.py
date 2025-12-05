from wordwield     import ww
from wordwield.lib import O


class Corrector(ww.operators.Agent):
	verbose = False
	
	class ResponseSchema(O):
		corrected_text: str

	template = '''
		Исправь несвязность речи, языковые ошибки и смысловые несоответствия.
		Сохрани стиль персонажа.
		Убедись, что изречение имеет целостный смысл и написано на ПРАВИЛЬНОМ РУССКОМ ЯЗЫКЕ
		НАЧАЛО ТЕКСТА
		-----------
		{{ text }}
		-----------
		КОНЕЦ ТЕКСТА
		'''

	async def invoke(self, text):
		return await self.ask()
