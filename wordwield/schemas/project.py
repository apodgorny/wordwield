from time import time

from typing import Optional

from wordwield.lib.o import O


class BeatSchema(O):
	timestamp : int = O.Field(description='Time of occurrence',       llm=False, semantic=True)
	text      : str = O.Field(description='Content of the utterance', llm=True,  semantic=True)
	
	def to_prompt(self):
		return f'[{self.persona}]: "{self.text}"'
	
	@classmethod
	def on_create(cls, data):
		data['timestamp'] = int(time())
		return data

class VariableSchema(O):
	varname : str
	streams : list[str]
	length  : Optional[int] = None

class StreamSchema(O):
	name     : str              = O.Field(semantic=True, description='Thread name', llm=False)
	triggers : str              = O.Field(semantic=True, description='Persona name who responds on writing', llm=False, default=None)
	beats    : Optional[list[BeatSchema]] = O.Field(semantic=True, description='Ordered sequence of thoughts or utterances', default_factory=list, llm=False)

	def to_list(self):
		return [beat.text for beat in self.beats]

class ExpertSchema(O):
	name           : str                            = O.Field(description='Character name',   semantic=True)
	mode           : str                            = O.Field(description='Agent mode, binary or unary', semantic=True)
	template       : str                            = O.Field(description='Agent template')
	read           : Optional[list[VariableSchema]] = O.Field(description='Streams names for persona to read from', default_factory=list)
	write          : Optional[list[VariableSchema]] = O.Field(description='Streams names for persona to write to',  default_factory=list)
	write_true     : Optional[list[VariableSchema]] = O.Field(description='Streams names for persona to write to',  default_factory=list)
	write_false    : Optional[list[VariableSchema]] = O.Field(description='Streams names for persona to write to',  default_factory=list)
	response_type  : str                            = O.Field(description='LLM response type')

class ProjectSchema(O):
	name     : str
	agents   : list[ExpertSchema]  = O.Field(semantic=True, description='All active personas in the timeline')
	streams  : list[StreamSchema] = O.Field(semantic=True, description='All active streams in the timeline')

class BinaryModeSchema(O):
	is_true : bool
	comment : str
