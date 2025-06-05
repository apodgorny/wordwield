from wordwield.lib.o import O


###########################################################################################

class VoiceSchema(O):
	name        : str             = O.Field(semantic=True, description='Имя или ярлык голоса')
	tone        : str             = O.Field(semantic=True, description='Эмоциональный окрас')
	style       : str             = O.Field(semantic=True, description='Речевая подача')
	intent      : str             = O.Field(semantic=True, description='Что голос хочет донести')

class BeatSchema(O):
	timestamp : int               = O.Field(semantic=True, description='Время появления')
	text      : str               = O.Field(semantic=True, description='Содержимое высказывания')

###########################################################################################

class ThreadSchema(O):
	voice : VoiceSchema           = O.Field(semantic=True, description='Источник голоса')
	beats : list[BeatSchema]      = O.Field(semantic=True, description='Последовательные мысли')

class TimelineSchema(O):
	title   : str                 = O.Field(semantic=False, description='Название временной линии')
	threads : list[ThreadSchema]  = O.Field(semantic=True,  description='Все активные потоки')

class CharacterSchema(O):
	name   : str                  = O.Field(semantic=True, description='Имя персонажа')
	voices : list[VoiceSchema]    = O.Field(semantic=True, description='Голоса, принадлежащие персонажу')


###########################################################################################

class SituationSchema(O):
	time       : str                   = O.Field(semantic=True, description='Описание времени: день, эпоха, утро и т.п.')
	location   : str                   = O.Field(semantic=True, description='Ключевое место действия')
	condition  : str                   = O.Field(semantic=True, description='Главное напряжение или положение вещей')
	characters : list[CharacterSchema] = O.Field(semantic=True, description='Какие персонажи участвуют')

class SceneSchema(O):
	title    : str                = O.Field(semantic=True, description='Название сцены')
	start    : SituationSchema    = O.Field(semantic=True, description='Начальная ситуация')
	end      : SituationSchema    = O.Field(semantic=True, description='Конечная ситуация')
	timeline : TimelineSchema     = O.Field(semantic=True, description='Временная линия сцены')
