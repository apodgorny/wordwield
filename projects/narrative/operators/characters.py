from wordwield import ww


class Characters(ww.operators.Agent):
	agents = {
		'character_factory' : ww.operators.character.Factory
	}
		
	async def invoke(self):
		schema = ww.schemas.CharacterFunctionSchema.put(name='characters')
		await self.agents.character_factory(schema)
		print(schema.to_yaml())
