from wordwield     import ww
from wordwield.core import O


class Spirit(ww.operators.Agent):
	class ResponseSchema(O):
		beat: str

	intent   = ''
	template = '''
		'''

	async def invoke(self, scene):
		return await self.ask()
