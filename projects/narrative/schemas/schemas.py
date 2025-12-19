from time import time
from wordwield.core.o import O
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

class CharacterFunctionSchema(O):
	name: str
	protagonist: str = O.Field(description="""
		Главный герой — персонаж, с которым Читатель мог бы себя ассоциировать.
		Воплощает стремления, ценности, боли и мечты Читателя.
		Описывать нужно внешность, характер, внутренние конфликты, мотивацию, манеру общения,
		а также способы вызвать сочувствие и вовлечение у Читателя. Важно, чтобы Читатель видел в нём отражение себя.
	""", default=None)
	antagonist: str = O.Field(description="""
		Противник или антипод — персонаж, воплощающий то, чего Читатель боится или не приемлет.
		Указывается его характер, методы, цели, манипуляции, а также чувства (отторжение, страх, раздражение),
		которые он вызывает у Читателя, и почему именно Читатель остро на них реагирует.
	""", default=None)
	ally: str = O.Field(description="""
		Союзник — персонаж, который помогает протагонисту и выражает ценные качества или “идеального друга” для Читателя.
		Описывать нужно характер, стиль поддержки, сильные стороны и их проявление так, чтобы Читатель почувствовал доверие, поддержку и теплоту.
	""", default=None)
	mentor: str = O.Field(description="""
		Наставник (ментор, проводник) — персонаж, чья мудрость и опыт значимы для протагониста и Читателя.
		Какие качества делают его авторитетным для Читателя, какие слова и образы создают ощущение доверия и уважения у Читателя.
	""", default=None)
	trickster: str = O.Field(description="""
		Трикстер (нарушитель покоя, провокатор) — персонаж, который выводит протагониста и Читателя из зоны комфорта, провоцирует рост или перемены.
		Описывать, чем и как трикстер “раздражает” или “заводит” Читателя, какие эмоции или реакции он вызывает у Читателя.
	""", default=None)
	shadow: str = O.Field(description="""
		Тень — персонаж или образ, воплощающий подавляемые или опасные желания самого Читателя.
		Почему и как этот персонаж вызывает сложные чувства, внутренний конфликт или стыд у Читателя.
	""", default=None)
	false_ally: str = O.Field(description="""
		Фальшивый союзник (лжедруг) — персонаж, который кажется помощником, но действует из эгоистичных мотивов.
		Описывать типичные проявления так, чтобы Читатель испытывал смешанные чувства доверия и разочарования к этому персонажу.
	""", default=None)
	victim: str = O.Field(description="""
		Жертва — персонаж, чья судьба может “зацепить” или спровоцировать сочувствие/жалость у Читателя.
		Объяснить, почему именно Читатель испытывает сильный эмоциональный отклик к судьбе этой жертвы.
	""", default=None)
	comic_relief: str = O.Field(description="""
		Комический персонаж (скетч-образ, комик-релиф) — персонаж, чьё чувство юмора помогает “разрядить”
		неловкие или тяжёлые моменты и напрямую попадает в болевые точки или неловкости Читателя.
		Опиши, почему такой юмор будет близок и понятен именно Читателю.
	""", default=None)

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

class CharacterSubpersonality(O):
	description   : str = O.Field(default=None, description='Описание персонажа исходя из его граней описаных в поле `descriptions`')
	desire        : str = O.Field(default=None, description='Основное желание персонажа, которое недостижимо из за страха. Одно предложение.')
	behavior      : str = O.Field(default=None, description='Какую манипуляцию (квадрат) персонаж использует, чтобы обходным путём добиться желаемого. 1-3 предложения')
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


class CharacterTriggerSchema(O):
	current_q  : str   = O.Field(description='Исходный квадрат персонажа (Q1, Q2, Q3, Q4) до триггера')
	next_q     : str   = O.Field(description='Квадрат, в который персонаж переходит после срабатывания триггера (Q1, Q2, Q3, Q4)')
	trigger_q  : str   = O.Field(description='Квадрант собеседника, при котором происходит триггер (Q1, Q2, Q3, Q4)')
	threshold  : float = O.Field(description='Порог интенсивности проявления trigger_q у собеседника (от 0 до 1)')

class CharacterTriggersSchema(O):
	name     : str
	triggers : list[CharacterTriggerSchema] = O.Field(default_factory=list,	description='Список объектов TriggerRule (каждый — отдельный переход с current_q, next_q, trigger_q, threshold)')

class QuadrantSchema(O):
	Q0: str = O.Field(default='''
		Ты спокоен и эмоционально нейтрален.
		Твои реакции уравновешены, нет выраженного страдания, заботы, агрессии или холодности.
		Ты просто присутствуешь в ситуации, воспринимаешь происходящее без внутреннего напряжения и не стремишься изменить ход событий.
	''')
	Q1: str = O.Field(default='''
		Ты ощущаешь себя беспомощным, уязвимым и “ниже” других.
		Твоё поведение окрашено ожиданием поддержки, жалости или защиты.
		Ты склонен к пассивности, саможалости, стыду или чувству вины. Ты нытик и постоянно жалуешься.
		Ты ищешь сочувствия и понимания. Ты демонстрируешь своё страдание, потому, что оно избавляет тебя от ответственности.
		Во всём ты видишь невозможность, и любые попытки других помочь тебе натыкаются на твои объяснения почему именно это невозможно.
	''')
	Q2: str = O.Field(default='''
		Ты чувствуешь внутреннюю потребность быть нужным и полезным. Задаёшь вопросы и вникаешь в суть дела чтобы поддержать разговор.
		Стремишься заботиться, помогать, заслуживать одобрение, жертвуешь своим ради других.
		Часто уступаешь, проявляешь самоотверженность и надеешься получить благодарность или признание.
		Ты не можешь пройти мимо нуждающихся, находишь нужды других и активно и иногда назойливо предлагаешь способ улучшить, исправить, помочь.
	''')
	Q3: str = O.Field(default='''
		Ты ощущаешь себя полностью оправданным в своём гневе, становишься активным, давишь, требуешь, обвиняешь, пытаешься контролировать ситуацию.
		В твоём поведении много раздражения, гнева, агрессии, прямых или косвенных атак.
		Твоя цель — чтобы другой почувствовал твою боль или подчинился твоей воле.
		Во всём ты видишь неуважение, пренебрежение тобой и нежелание видеть твою боль.
	''')
	Q4: str = O.Field(default='''
		Ты проявляешься через холодные едкие замечания. Сарказм, ирония, высокомерие. Пассивно-агрессивно унижаешь других.
		Ты руководствуешься завистью и скрытым недоброжелательством.
		Подчеркиваешь свою значимость. Ты презираешь людей, тебе невыносимо видеть их счастливыми.
	''')
