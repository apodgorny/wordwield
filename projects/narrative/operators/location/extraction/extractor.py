from wordwield.core import O, Operator, String
from wordwield     import ww


class Extractor(ww.operators.Agent):

	agents = {
		'location_name_extractor'         : ww.operators.location.extraction.Names,
		'location_description_extractor'  : ww.operators.location.extraction.Descriptions,
		'location_dup_extractor'          : ww.operators.location.extraction.Duplicates,
	}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.descriptions = {}    # canonical name : [descriptions]
		self.names        = {}    # canonical name : set(alternative names)

	async def extract_duplicates(self, text):
		return await self.agents.location_dup_extractor(
			keys  = self.names,
			text  = text,
			names = self.names
		)

	async def extract_names(self, text):
		return await self.agents.location_name_extractor(
			text  = text,
			names = self.names
		)
	
	async def extract_descriptions(self, text, name):
		return await self.agents.location_description_extractor(
			text          = text,
			location_name = name
		)

	async def extract_locations(self, text):
		names = await self.extract_names(text)    
		if self.names:
			duplicates = await self.extract_duplicates(text)
			for name in duplicates:
				if not name in self.names:
					self.names[name] = set()
				self.names[name].add(duplicates[name])
		else:
			self.names = { name: set() for name in names }

		for name in self.names:
			if name not in self.descriptions: self.descriptions[name] = []
			descriptions = await self.extract_descriptions(text, name)
			self.descriptions[name] += descriptions

	def save_locations(self):
		for name in self.names:
			self.ww.schemas.LocationSchema.put(
				name         = name,
				alt_names    = list(self.names[name]),
				descriptions = self.descriptions[name]
			)

	async def invoke(self, texts):
		for text in texts:
			await self.extract_locations(text)
		self.save_locations()

		print('-'*40)
		print('LOCATIONS:')
		print('-'*40)
		print(f'NAMES: {self.names}')
		print(f'DESCRIPTIONS: {self.descriptions}')
		print('-'*40)
