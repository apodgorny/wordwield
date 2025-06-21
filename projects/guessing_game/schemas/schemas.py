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

###########################################################################################

class NumberSchema(O):
	guessed_number: int

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
