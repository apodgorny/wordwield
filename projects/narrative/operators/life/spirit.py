from wordwield     import ww
from wordwield.lib import O


class Spirit(ww.operators.Agent):
	class ResponseSchema(O):
		beat: str

	intent   = ''
	template = '''
		'''

	async def invoke(self, scene):
		return await self.ask()
