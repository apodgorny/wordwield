from wordwield import ww
from wordwield.lib.model import Model


class Narrative(ww.operators.Project):
	intent      = 'Создать захватывающий нарратив'
	description = ''
	agents      = {
		'story_planner'               : ww.operators.story.Planner,
		'character_extractor'         : ww.operators.character.extraction.Extractor,
		'location_extractor'          : ww.operators.location.extraction.Extractor,
		'character_developer'         : ww.operators.character.development.Developer,
		# 'character_mission_developer' : ww.operators.character.development.MissionDeveloper
	}
	streams = []

	async def invoke(self):
		completion = ww.schemas.CompletionSchema.put(self.name)
		story      = ww.schemas.StorySchema.get(self.name)

		if not completion.story_preparation:
			print('STORY PREPARATION')
			Model.restart()
			await self.agents.story_planner(story)
			completion.set(story_preparation = True)

		if not completion.character_extraction:
			print('CHARACTER EXTRACTION')
			Model.restart()
			await self.agents.character_extractor([story.beginning, story.middle, story.end])
			completion.set(character_extraction = True)

		if not completion.location_extraction:
			print('LOCATION EXTRACTION')
			Model.restart()
			await self.agents.location_extractor([story.beginning, story.middle, story.end])
			completion.set(location_extraction = True)

		if not completion.character_development:
			print('CHARACTER DEVELOPMENT')
			Model.restart()
			characters = ww.schemas.CharacterSchema.all()
			for name in characters:
				await self.agents.character_developer(characters[name])
			completion.set(character_development = True)

		if not completion.scene_development:
			print('SCENE DEVELOPMENT')
			# for scene in story.scenes:
			# 	print(scene)

		# characters = ww.schemas.CharacterSchema.all()
		# for name in characters:
		# 	print(characters[name])

		return 1