from wordwield.lib       import O, Operator
from wordwield.operators import Project


class Narrative(Project):

	async def extract_characters(self, texts):
		names        = []
		descriptions = {}
		for text in texts:
			names_schema = self.ww.schemas.CharacterNamesSchema(names=names)
			new_names    = await self.agents.character_name_extractor(
				data   = dict(text=text),
				schema = names_schema
			)
			for char_name in new_names:
				if char_name not in descriptions: descriptions[char_name] = []
				descr_schema = self.ww.schemas.CharacterDescriptionSchema(descriptions=descriptions[char_name])
				new_descr = await self.agents.character_description_extractor(
					data   = dict(text=text, character_name=char_name),
					schema = descr_schema
				)
				descriptions[char_name] += new_descr
			names = list(set(names + new_names))

	async def invoke(self):
		story = self.ww.schemas.StorySchema.load(self.name)
		if story.middle is None:
			await self.agents.planner(self.name, self.ww.schemas.StorySchema)
			
		await self.extract_characters([story.beginning, story.middle, story.end])
		
		print('RESULT:', names)
		print(descriptions)