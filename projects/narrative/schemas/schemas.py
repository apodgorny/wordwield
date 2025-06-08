import time
from wordwield.lib.o import O
from typing import Optional

###########################################################################################

class VoiceSchema(O):
	name   : str = O.Field(semantic=True, description='Name or label of the voice')
	tone   : str = O.Field(semantic=True, description='Emotional coloring')
	style  : str = O.Field(semantic=True, description='Speech style or delivery')
	intent : str = O.Field(semantic=True, description='What the voice is trying to convey')

class BeatSchema(O):
	timestamp : int = O.Field(llm=False, semantic=True, description='Time of occurrence')
	persona   : str = O.Field(llm=False, semantic=True, description='Persona name')
	voice     : str = O.Field(llm=False, semantic=True, description='Voice name')
	text      : str = O.Field(llm=True,  semantic=True, description='Content of the utterance')
	
	def to_prompt(self):
		return f'[{self.persona}]: "{self.text}"'
	
	@classmethod
	def on_create(cls, data):
		data['timestamp'] = int(time.time())
		return data

###########################################################################################

class ThreadSchema(O):
	beats: list[BeatSchema] = O.Field(semantic=True, description='Ordered sequence of thoughts or utterances')

	def __getitem__(self, idx) : return self.beats[idx]
	def __iter__(self)         : return iter(self.beats)
	def __len__(self)          : return len(self.beats)

class PersonaSchema(O):
	name   : str                         = O.Field(semantic=True, description='Character name')
	agent  : str                         = O.Field(semantic=True, description='Agent class name')
	voices : Optional[list[VoiceSchema]] = O.Field(semantic=True, description='Voices belonging to this character', default_factory=list)
	 
class TimelineSchema(O):
	personas : list[PersonaSchema] = O.Field(semantic=True, description='All active threads in the timeline')

###########################################################################################

class SituationSchema(O):
	time       : str                 = O.Field(semantic=True, description='Time description: day, era, morning, etc.')
	location   : str                 = O.Field(semantic=True, description='Key location')
	condition  : str                 = O.Field(semantic=True, description='Main tension or state of affairs')
	characters : list[PersonaSchema] = O.Field(semantic=True, description='Characters involved in the situation')

class SceneSchema(O):
	title    : str             = O.Field(semantic=True, description='Scene title')
	start    : SituationSchema = O.Field(semantic=True, description='Initial situation')
	end      : SituationSchema = O.Field(semantic=True, description='Final situation')
	timeline : TimelineSchema  = O.Field(semantic=True, description='Timeline of the scene')
