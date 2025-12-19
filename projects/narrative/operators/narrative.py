from wordwield import ww
from wordwield.core.model import Model


class Narrative(ww.operators.Agent):
	intent      = 'Создать захватывающий нарратив'
	description = ''
	agents      = {
		'story_planner'       : ww.operators.story.Planner,

		'character_extractor' : ww.operators.character.Extractor,
		'character_developer' : ww.operators.character.Developer,

		'location_extractor'  : ww.operators.location.extraction.Extractor,

		'scene_splitter'      : ww.operators.scene.development.Splitter,
		'scene_expander'      : ww.operators.scene.development.Expander,
		'scene_planner'       : ww.operators.scene.development.Planner,
		'beat_developer'      : ww.operators.scene.development.BeatDeveloper,
		'writer'              : ww.operators.scene.development.Writer,
		'scene_summarizer'    : ww.operators.scene.development.Summarizer,

		'spirit'              : ww.operators.life.Spirit,
		'character'           : ww.operators.life.Character,
		'director'            : ww.operators.life.Director,
		'summarizer'          : ww.operators.life.Summarizer,  # улучшить чтобы больше внимания уделять последним событиям
	}
	streams = [
		'scenes'
	]

	def get_scenes(self, as_dict=False)       : return ww.schemas.SceneSchema.all(as_dict=as_dict)
	def get_scene_drafts(self, as_dict=False) : return ww.schemas.SceneDraftSchema.all(as_dict=as_dict)
	def get_scene_beats(self, as_dict=False)  : return ww.schemas.SceneBeatsSchema.all(as_dict=as_dict)
	def get_characters(self, as_dict=False)   : return ww.schemas.CharacterSchema.all(as_dict=as_dict)

	def get_character_names(self):
		scenes = self.get_scenes()
		character_names = set()
		for scene in scenes:
			character_names.update(scene.characters)
		return list(character_names)
	
	async def invoke(self):
		completion = ww.schemas.CompletionSchema.put(self.name)
		story      = ww.schemas.StorySchema.get(self.name)

		if not completion.story_preparation:
			print('STORY PREPARATION')
			await self.agents.story_planner(story)
			completion.set(story_preparation = True)

		if not completion.scene_preparation:
			print('SCENE PREPARATION')
			scenes = await self.agents.scene_splitter(story=story, scene_count=20)
			for scene in scenes:
				scene.save()
			completion.set(scene_preparation = True)

		if not completion.scene_drafting:
			scenes = self.get_scenes()
			print('SCENE DRAFTING', len(scenes), type(scenes[0]))
			previous_scenes = []
			summary         = None
			for scene in scenes:
				scene_text = await self.agents.writer(
					summary = summary,
					story   = story,
					scene   = scene
				)
				previous_scenes.append(scene_text)
				self.streams.scenes.write(scene_text)
				summary = await self.agents.scene_summarizer(scenes=previous_scenes)
				ww.schemas.SceneDraftSchema.put(
					name      = scene.name,
					backstory = summary,
					text      = scene_text,
				)
			completion.set(scene_drafting = True)

		if not completion.character_extraction:
			print('CHARACTER EXTRACTION')
			character_names = self.get_character_names()
			scene_drafts    = self.get_scene_drafts()
			descriptions    = {}
			for draft in scene_drafts:
				for character_name in character_names:
					more_descriptions = await self.agents.character_extractor(
						character_name = character_name,
						text           = draft.text
					)
					descriptions[character_name] = descriptions.get(character_name, []) + more_descriptions
			completion.set(character_extraction = True)

		if not completion.character_development:
			print('CHARACTER DEVELOPMENT')
			character_names = self.get_character_names()
			for character_name in character_names:
				character = ww.schemas.CharacterSchema.put(
					name         = character_name,
					descriptions = descriptions[character_name]
				)
				await self.agents.character_developer(character)
			completion.set(character_development = True)

		if not completion.life:
			print('LIFE')
			characters = self.get_characters(as_dict=True)
			scenes     = self.get_scenes()
			for scene in scenes:
				scene_characters = [characters[character_name] for character_name in scene.characters]
				for character in scene_characters:
					summary = await self.agents.summarizer(scenes=previous_scenes)
					await self.agents.director(scene)
					summary = await self.agents.summarizer(scenes=previous_scenes)
					await self.agents.character(character, scene)


		# if not completion.scene_development:
		# 	scene_drafts       = self.get_scene_drafts()
		# 	previous_sentences = []
		# 	for draft in scene_drafts:
		# 		sentences = [s.text for s in sentenize(draft.text)]
		# 		beats     = []
		# 		for sentence in sentences:
		# 			new_beats = await self.agents.beat_developer(sentence, previous_sentences)
		# 			beats += new_beats
		# 			previous_sentences.append(sentence)

		# 		ww.schemas.SceneBeatsSchema.put(
		# 			name  = draft.name,
		# 			beats = beats
		# 		)
		# 		for beat in beats:
		# 			print ('BEAT', beat)
		# 	completion.set(scene_development = True)

		# all_scene_beats = self.get_scene_beats()
		# for scene_beats in all_scene_beats:
		# 	scene_name = scene_beats.name
		# 	for beat in scene_beats.beats:



		# characters = ww.schemas.CharacterSchema.all()
		# for name in characters:
		# 	print(characters[name])

		return 1