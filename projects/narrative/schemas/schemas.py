from time import time
from wordwield.lib.o import O
from typing import Optional


class CompletionSchema(O):
	name                  : str
	story_preparation     : bool = False
	scene_preparation     : bool = False
	scene_drafting        : bool = False

	location_extraction   : bool = False
	character_extraction  : bool = False
	character_development : bool = False

	scene_development     : bool = False

###########################################################################################

class VoiceSchema(O):
	name   : str = O.Field(semantic=True, description='Name or label of the voice')
	tone   : str = O.Field(semantic=True, description='Emotional coloring')
	style  : str = O.Field(semantic=True, description='Speech style or delivery')
	intent : str = O.Field(semantic=True, description='What the voice is trying to convey')
	prompt : str

###########################################################################################

class StorySchema(O):
	name      : str = O.Field(default=None, description='Краткий идентификатор или уникальное имя этой истории.')
	title     : str = O.Field(default=None, description='Полное, формальное название истории, как оно будет представлено читателям.')
	genre     : str = O.Field(default=None, description='Литературный жанр или категория истории (например, историческая драма, комедия, научная фантастика).')
	time      : str = O.Field(default=None, description='Привлизительное время действия')
	place     : str = O.Field(default=None, description='Приблизительное место действия')
	moral     : str = O.Field(default=None, description='Мораль истории, красная нить, которая накаляется, прячется и появляется снова по ходу истории, которая становится явной и неотвратимой в развязке')
	problem   : str = O.Field(default=None, description='Общая проблема или конфликт на которой сфокусированы персонажи в течение всей истории')
	plot      : str = O.Field(default=None, description='Краткое изложение основного сюжета и ключевых событий.')
	outcome   : str = O.Field(default=None, description='Финал истории, развязка, к которой всё движется. Финал должен быть глубоко удовлетворительным для читателя. Он должен быть окончательным а не prequelом')
	# beginning : str       = O.Field(default=None, description='Текст или краткое описание начальной части истории.')
	# end       : str       = O.Field(default=None, description='Текст или краткое описание заключительной или финальной части истории.')
	# middle    : str       = O.Field(default=None, description='Текст или краткое описание того, как развивается история и соединяет начало и конец.')

class CharacterSchema(O):
	name          : str
	descriptions  : list[str]
	description   : str = O.Field(default=None, description='Описание персонажа исходя из его граней описаных в поле `descriptions`')
	fear          : str = O.Field(default=None, description='Основной страх персонажа на который опирается его поведение. Одно предложение')
	desire        : str = O.Field(default=None, description='Основное желание персонажа, которое недостижимо из за страха. Одно предложение.')
	bypass        : str = O.Field(default=None, description='Какое искаженое поведение персонаж использует чтобы получить желаемое. Удаётся ли ему?')
	manipulation1 : str = O.Field(default=None, description='Какую манипуляцию (квадрат) персонаж использует, чтобы обходным путём добиться желаемого. 1-3 предложения')
	manipulation2 : str = O.Field(default=None, description='Когда первый способ не помогает, какую ДРУГУЮ манипуляцию (квадрат) персонаж использует, чтобы обходным путём добиться желаемого. 1-3 предложения')
	resource      : str = O.Field(default=None, description='Эмоциональный Ресурс. В 2-3 слова описание внутреннего эмоционального состояния которое персонаж пытается получить извне через свои стратегии манипуляции')
	trigger       : str = O.Field(default=None, description='Кнопки. В одно-два предложения: события, поведение других, неприятные мелочи которые "включают" в персонаже страх потери "ресурса" заставляющий применять манипуляции')
	voice1        : str = O.Field(default=None, description='Голос субличности1 не длиннее одного предложения. Если бы у первой стратегии (manipulation1) был голос, как бы она выразилась, что бы сказала, потребовала, попросила, о чем промолчала? (В ОДНО ПРЕДЛОЖЕНИЕ)')
	voice2        : str = O.Field(default=None, description='Голос субличности2 не длиннее одного предложения. Если бы у второй стратегии (manipulation2) был голос, как бы она выразилась, что бы сказала, потребовала, попросила, о чем промолчала? (В ОДНО ПРЕДЛОЖЕНИЕ), должен отличаться от voice1')
	problem       : str = O.Field(default=None, description='Текущая проблема жизни, которую невозможно обойти. Одно предложение')
	mission       : str = O.Field(default=None, description='Идея фикс. Конкретное действие, которое должно быть сделано. Необходимый результат который по мнению персонажа решит проблему "problem"')
	schtick       : str = O.Field(default=None, description='Личностная особенность, изюминка, фишечка персонажа')
	speech_style  : str = O.Field(default=None, description='Как персонаж выражает себя в разговоре, стиль юмора или его отсутствия')

class CharacterStateSchema(O):
	name            : str 
	long_emotion    : str = O.Field(default=None, description='Каково моё состояние с учетом всех событий?')
	fast_emotion    : str = O.Field(default=None, description='Что я чувствую прямо сейчас с учетом последних событий?')
	fast_desire     : str = O.Field(default=None, description='Что я хочу сделать прямо сейчас с учетом последних событий и моей особенности?')
	memo            : str = O.Field(default=None, description='Последние события, которые свежи в памяти с учётом моей особенности')
	last_action     : str = O.Field(default=None, description='Последние действия, которые свежи я сделал')
	last_words      : str = O.Field(default=None, description='Последние слова, которые я сказал и кому')
	last_impression : str = O.Field(default=None, description='Последние впечатления о происходящем')

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

class SceneSchema(O):
	name                : str       = O.Field(default=None, description='Титул сцены')
	emotional_backstory : str       = O.Field(default=None, description='Эмоциональное состояние героев прошлой сцены влияет на события, желания текущей.')
	backstory           : str       = O.Field(default=None, description='Развязка предыдущей сцены приводит к началу текущей. 1 предложение.')
	setting             : str       = O.Field(default=None, description='Место, время и обстоятельства сцены (опционально)')
	characters          : list[str] = O.Field(default=None, description='Список имён персонажей, участвующих в сцене (опционально)')
	meta                : str       = O.Field(default=None, description='Название стадия драматургической прогрессии для этой сцены')
	problem             : str       = O.Field(default=None, description='Проблема или неудобство, которое преодолевается/преодолевается/нарастает в этой сцене')
	peak                : str       = O.Field(default=None, description='Накал, Пиковый момент через который происходит развязка')
	outcome             : str       = O.Field(default=None, description='Развязка сцены - однозначный результат: Открытие, осознание, принятое решение или действие')
	emotional_outcome   : str       = O.Field(default=None, description='Эмоциональный фон итога сцены для персонажей')
	description         : str       = O.Field(default=None, description='Описание сцены без подробностей, как сценарий')
	plot                : str       = O.Field(default=None, description='Последовательность внешних обстоятельств, которые заставляют персонажей прийти к итогу сцены, шаг за шагом')

class SceneDraftSchema(O):
	name                : str       = O.Field(default=None, description='Титул сцены')
	backstory           : str       = O.Field(default=None, description='Краткое содержание предыдущих сцен')
	text                : str       = O.Field(default=None, description='Текст драфта сцены')

class SceneBeat(O):
	character : str
	action    : str

class SceneBeatsSchema(O):
	name  : str             = O.Field(default=None, description='Титул сцены')
	beats : list[SceneBeat] = O.Field(default=None, description='Биты сцены')

