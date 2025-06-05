from wordwield.lib.o import O

###########################################################################################

class VoiceSchema(O):
    name   : str = O.Field(semantic=True, description='Name or label of the voice')
    tone   : str = O.Field(semantic=True, description='Emotional coloring')
    style  : str = O.Field(semantic=True, description='Speech style or delivery')
    intent : str = O.Field(semantic=True, description='What the voice is trying to convey')

class BeatSchema(O):
    timestamp : int = O.Field(semantic=True, description='Time of occurrence')
    text      : str = O.Field(semantic=True, description='Content of the utterance')

###########################################################################################

class ThreadSchema(O):
    voice : VoiceSchema        = O.Field(semantic=True, description='Source voice')
    beats : list[BeatSchema]   = O.Field(semantic=True, description='Ordered sequence of thoughts or utterances')

class TimelineSchema(O):
    title   : str                = O.Field(semantic=False, description='Timeline title')
    threads : list[ThreadSchema] = O.Field(semantic=True, description='All active threads in the timeline')

class CharacterSchema(O):
    name   : str                = O.Field(semantic=True, description='Character name')
    voices : list[VoiceSchema]  = O.Field(semantic=True, description='Voices belonging to this character')

###########################################################################################

class SituationSchema(O):
    time       : str                      = O.Field(semantic=True, description='Time description: day, era, morning, etc.')
    location   : str                      = O.Field(semantic=True, description='Key location')
    condition  : str                      = O.Field(semantic=True, description='Main tension or state of affairs')
    characters : list[CharacterSchema]    = O.Field(semantic=True, description='Characters involved in the situation')

class SceneSchema(O):
    title    : str             = O.Field(semantic=True, description='Scene title')
    start    : SituationSchema = O.Field(semantic=True, description='Initial situation')
    end      : SituationSchema = O.Field(semantic=True, description='Final situation')
    timeline : TimelineSchema  = O.Field(semantic=True, description='Timeline of the scene')
