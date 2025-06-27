from wordwield import ww


class Narrative(ww.operators.Project):
	intent      = 'Создать захватывающий нарратив'
	description = ''
	agents      = {
		'story_planner'               : ww.operators.story.Planner,
		'character_extractor'         : ww.operators.character.extraction.Extractor,
		'location_extractor'          : ww.operators.location.extraction.Extractor,
		'character_developer'         : ww.operators.character.development.Developer,
		'character_mission_developer' : ww.operators.character.development.MissionDeveloper
	}
	streams = []

	async def invoke(self):
		completion = ww.schemas.CompletionSchema.put(self.name)
		story      = ww.schemas.StorySchema.get(self.name)

		if not completion.story_preparation:
			await self.agents.story_planner(story)
			completion.set(story_preparation = True)

		if not completion.character_extraction:
			await self.agents.character_extractor([story.beginning, story.middle, story.end])
			completion.set(character_extraction = True)

		if not completion.location_extraction:
			await self.agents.location_extractor([story.beginning, story.middle, story.end])
			completion.set(location_extraction = True)

		if not completion.character_development:
			characters = ww.schemas.CharacterSchema.all()
			for name in characters:
				await self.agents.character_developer(characters[name])
			completion.set(character_development = True)

		if not completion.character_mission_development:
			characters = ww.schemas.CharacterSchema.all()
			text       = '\n'.join([story.beginning, story.middle, story.end])
			missions   = {}

			for name in characters:
				mission = await self.agents.character_mission_developer(
					missions  = missions,
					character = characters[name],
					text      = text
				)
				missions[name] = mission
				characters[name].set(mission = mission)
			# completion.set(character_mission_development = True)

		# if not completion.scene_development:
		# 	for scene in story.scenes:
		# 		print(scene)

		return 1