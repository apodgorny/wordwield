from wordwield import ww
from wordwield.lib.model import Model


class Life(ww.operators.Project):
	description = ''
	agents = {
		'character' : ww.operators.Character,
		'spirit'    : ww.operators.Spirit
	}

	async def invoke(self):
		history = self.ww.schemas.StreamSchema.zip(
			self.agents.spirit.streams.stream.name,
			self.agents.character.streams.stream.name
		).read()

		for g in history:
			print(f'{g.author}: "{g.value}"')

		# await self.agents.spirit    ('Дух',  history=history)
		# await self.agents.character ('Хосе', history=history)

		# history = self.ww.schemas.StreamSchema.zip(
		# 	self.agents.spirit.streams.stream.name,
		# 	self.agents.character.streams.stream.name
		# ).read()

		# print(history)

