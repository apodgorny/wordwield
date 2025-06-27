from time import time
from wordwield.lib.o import O
from typing import Optional


class CompletionSchema(O):
	name                          : str
	story_preparation             : bool = False
	character_extraction          : bool = False
	location_extraction           : bool = False
	character_development         : bool = False
	character_mission_development : bool = False
	scene_development             : bool = False

###########################################################################################

class VoiceSchema(O):
	name   : str = O.Field(semantic=True, description='Name or label of the voice')
	tone   : str = O.Field(semantic=True, description='Emotional coloring')
	style  : str = O.Field(semantic=True, description='Speech style or delivery')
	intent : str = O.Field(semantic=True, description='What the voice is trying to convey')
	prompt : str

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

class CharacterSchema(O):
	name         : str
	alt_names    : list[str]
	descriptions : list[str]
	mission      : str
	fear         : str       = O.Field(default=None, description='Глубокий страх персонажа на который опирается его поведение. Одно предложение')
	desire       : str       = O.Field(default=None, description='Глубокое желание персонажа, которое недостижимо из за страха. Одно предложение.')
	bypass       : str       = O.Field(default=None, description='Как персонаж добивается части желаемого в обход своего страха')
	strategy1    : str       = O.Field(default=None, description='Какую манипуляцию персонаж использует, чтобы обходным путём добиться желаемого. 1-3 предложения')
	strategy2    : str       = O.Field(default=None, description='Когда первый способ не помогает, какую ДРУГУЮ манипуляцию персонаж использует, чтобы обходным путём добиться желаемого. 1-3 предложения')
	square1      : int       = O.Field(default=None, description='Номер квадрата (1-4) для первой стратегии - strategy1 по принципу Квадрат Подгорного')
	square2      : int       = O.Field(default=None, description='Номер квадрата (1-4) для второй стратегии - strategy2 по принципу Квадрат Подгорного')
	resource     : str       = O.Field(default=None, description='Эмоциональный Ресурс. В 2-3 слова описание внутреннего эмоционального состояния которое персонаж пытается получить извне через свои стратегии манипуляции')
	trigger      : str       = O.Field(default=None, description='Кнопки. В одно-два предложения: события, поведение других, неприятные мелочи которые "включают" в персонаже страх потери "ресурса" заставляющий применять манипуляции')
	voice1       : str       = O.Field(default=None, description='Голос субличности 1 не длиннее одного предложения. Если бы у первой стратегии (strategy1) был голос, как бы она выразилась, что бы сказала, потребовала, попросила, о чем промолчала? (В ОДНО ПРЕДЛОЖЕНИЕ)')
	voice2       : str       = O.Field(default=None, description='Голос субличности 2 не длиннее одного предложения. Если бы у второй стратегии (strategy2) был голос, как бы она выразилась, что бы сказала, потребовала, попросила, о чем промолчала? (В ОДНО ПРЕДЛОЖЕНИЕ)')


class LocationSchema(O):
	name         : str
	alt_names    : list[str]
	descriptions : list[str]

###########################################################################################

# class SituationSchema(O):
# 	time       : str               = O.Field(semantic=True, description='Time description: day, era, morning, etc.')
# 	location   : str               = O.Field(semantic=True, description='Key location')
# 	condition  : str               = O.Field(semantic=True, description='Main tension or state of affairs')
# 	characters : list[AgentSchema] = O.Field(semantic=True, description='Characters involved in the situation')

# class SceneSchema(O):
# 	name     : str
# 	title    : str             = O.Field(semantic=True, description='Scene title in 1–3 words')
# 	start    : SituationSchema = O.Field(semantic=True, description='Initial situation')
# 	end      : SituationSchema = O.Field(semantic=True, description='Final situation')
