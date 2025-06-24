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

class StorySchema(O):
	name      : str       = O.Field(default=None, description='Краткий идентификатор или уникальное имя этой истории.')
	title     : str       = O.Field(default=None, description='Полное, формальное название истории, как оно будет представлено читателям.')
	genre     : str       = O.Field(default=None, description='Литературный жанр или категория истории (например, драма, комедия, научная фантастика).')
	plot      : str       = O.Field(default=None, description='Краткое изложение основного сюжета и ключевых событий.')
	beginning : str       = O.Field(default=None, description='Текст или краткое описание начальной части истории.')
	end       : str       = O.Field(default=None, description='Текст или краткое описание заключительной или финальной части истории.')
	middle    : str       = O.Field(default=None, description='Текст или краткое описание того, как развивается история и соединяет начало и конец.')
	scenes    : list[str] = O.Field(default=None, description='Список ключевых сцен, каждая кратко описана строкой, в повествовательном порядке.')

class CharacterNamesSchema(O):
	# name            : str       = O.Field(llm=False)
	names : list[str] = O.Field(llm=True, description='Список имён упомянутых персонажей', default_factory=list)

class CharacterDescriptionSchema(O):
	descriptions : list[str] = O.Field(llm=True, description='Описания из текста характеризуюие персонажа', default_factory=list)

class ScheneSchema(O):
	...

class ScenerySchema(O):
	scenes : list[ScheneSchema]



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
