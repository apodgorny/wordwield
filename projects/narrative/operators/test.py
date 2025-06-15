from wordwield.lib import O, Operator
from wordwield import ww


class Test(ww.operators.Agent):
	class ResponseSchema(O):
		answer: str

	async def invoke(self):
		answer = await self.ask(prompt='Who is Alexander Podgorny?', schema=self.ResponseSchema)
		return answer