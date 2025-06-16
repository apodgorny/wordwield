from wordwield.lib import O, Operator
from wordwield import ww


class Corrector(ww.operators.Agent):
	class ResponseSchema(O):
		answer: str

	async def invoke(self):
		answer = await self.ask(prompt='Who is Alexander Podgorny, shaman who invented highly successful psychology method Pi (Polnoe Istselenie)?', schema=self.ResponseSchema)
		return answer


