from wordwield import ww


class Narrative(ww.operators.Project):
	intent      = 'Создать захватывающий нарратив'
	description = ''
	agents      = {
		'planner'                         : ww.operators.Planner,
		'character_extractor'             : ww.operators.CharacterExtractor,
		'character_name_extractor'        : ww.operators.CharacterNameExtractor,
		'character_description_extractor' : ww.operators.CharacterDescriptionExtractor,
		'character_dup_extractor'         : ww.operators.CharacterDupExtractor
	}
	streams = []

	async def invoke(self):
		completion = ww.schemas.CompletionSchema.get(self.name)
		completion.set(story_preparation = True)
		story      = ww.schemas.StorySchema.get(self.name)

		if not completion.story_preparation:
			await self.agents.planner(self.name, self.ww.schemas.StorySchema)
			completion.set(story_preparation = True)

		if not completion.character_extraction:
			await self.agents.character_extractor([story.beginning, story.middle, story.end])
			completion.set(character_extraction = True)

		return 1