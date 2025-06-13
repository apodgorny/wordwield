from time import time
from wordwield.lib.o import O
from typing import Optional

###########################################################################################

class VoiceSchema(O):
	name   : str = O.Field(semantic=True, description='Name or label of the voice')
	tone   : str = O.Field(semantic=True, description='Emotional coloring')
	style  : str = O.Field(semantic=True, description='Speech style or delivery')
	intent : str = O.Field(semantic=True, description='What the voice is trying to convey')
	prompt : str

class BeatSchema(O):
	timestamp : int = O.Field(description='Time of occurrence',       llm=False, semantic=True)
	text      : str = O.Field(description='Content of the utterance', llm=True,  semantic=True)
	
	def to_prompt(self):
		return f'[{self.persona}]: "{self.text}"'
	
	@classmethod
	def on_create(cls, data):
		data['timestamp'] = int(time())
		return data

###########################################################################################

class VariableSchema(O):
	varname : str
	threads : list[str]
	length  : Optional[int] = None

class StreamSchema(O):
	name     : str              = O.Field(semantic=True, description='Thread name', llm=False)
	triggers : str              = O.Field(semantic=True, description='Persona name who responds on writing', llm=False, default=None)
	beats    : Optional[list[BeatSchema]] = O.Field(semantic=True, description='Ordered sequence of thoughts or utterances', default_factory=list, llm=False)

	def __getitem__(self, idx) : return self.beats[idx]
	def __iter__(self)         : return iter(self.beats)
	def __len__(self)          : return len(self.beats)

class AgentSchema(O):
	name           : str                   = O.Field(description='Character name',   semantic=True)
	type           : str                   = O.Field(description='Agent class name', semantic=True)
	template       : str                   = O.Field(description='Agent template')
	read  : Optional[list[VariableSchema]] = O.Field(description='Threads names for persona to read from', default_factory=list)
	write : Optional[list[VariableSchema]] = O.Field(description='Threads names for persona to write to',  default_factory=list)
	response_type  : str                   = O.Field(description='LLM response type')

class AgentSelectorSchema(AgentSchema):
	name           : str                         = O.Field(description='Character name', semantic=True)
	type           : str                         = O.Field(description='Agent class name', semantic=True)
	read  : Optional[list[VariableSchema]]         = O.Field(description='Threads names for persona to read from', default_factory=list)
	write_true : Optional[list[VariableSchema]]         = O.Field(description='Threads names for persona to write to',  default_factory=list)
	write_false : Optional[list[VariableSchema]]         = O.Field(description='Threads names for persona to write to',  default_factory=list)
	 
class TimelineSchema(O):
	name     : str
	agents   : list[AgentSchema]  = O.Field(semantic=True, description='All active personas in the timeline')
	streams  : list[StreamSchema] = O.Field(semantic=True, description='All active threads in the timeline')

class SelectorSchema(O):
	is_true : bool
	comment : str

###########################################################################################

# class SituationSchema(O):
# 	time       : str               = O.Field(semantic=True, description='Time description: day, era, morning, etc.')
# 	location   : str               = O.Field(semantic=True, description='Key location')
# 	condition  : str               = O.Field(semantic=True, description='Main tension or state of affairs')
# 	characters : list[AgentSchema] = O.Field(semantic=True, description='Characters involved in the situation')

# class SceneSchema(O):
# 	title    : str             = O.Field(semantic=True, description='Scene title')
# 	start    : SituationSchema = O.Field(semantic=True, description='Initial situation')
# 	end      : SituationSchema = O.Field(semantic=True, description='Final situation')
# 	timeline : TimelineSchema  = O.Field(semantic=True, description='Timeline of the scene')
