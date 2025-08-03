from wordwield import ww
from wordwield.lib.vdb import VDB


# character = ww.schemas.CharacterSchema.put(
# 	name          = 'Вася',
# 	descriptions  = ['простой хороший парень 35 лет'],
# 	description   = 'простой хороший парень 35 лет',
# 	fear          = 'боится не вписаться в общество',
# 	desire        = 'хочет быть нужным и любимым',
# 	bypass        = 'служение, по этому Вася изучает программирование',
# 	manipulation1 = 'служение, уваженительное обращение',
# 	manipulation2 = 'слёзы',
# 	resource      = 'нужность',
# 	trigger       = 'непринятый энтузиазм',
# 	voice1        = 'я хороший мальчик и многое могу дать',
# 	voice2        = 'я плохой и никому не нужен',
# 	problem       = 'страх общения',
# 	mission       = 'стать первоклассным программистом, тогда он будет нужен людям',
# 	schtick       = 'хороший ученик',
# 	speech_style  = 'заикание'
# )

sheldon = ww.schemas.CharacterTriggersSchema(
	name = 'Sheldon Cooper',
	triggers = [
		ww.schemas.CharacterTriggerSchema(current_q='Q4', next_q='Q3', trigger_q='Q3', threshold=0.5),   # Становится агрессивно-обесценивающим, если встречает агрессию
		ww.schemas.CharacterTriggerSchema(current_q='Q4', next_q='Q1', trigger_q='Q1', threshold=0.6),   # Проваливается в страдание, если сталкивается с демонстративной жертвенностью (например, мать или Эми в слезах)
		ww.schemas.CharacterTriggerSchema(current_q='Q4', next_q='Q2', trigger_q='Q2', threshold=0.7),   # Пытается заботиться и поддерживать, если кто-то начинает искренне служить или заботиться о нём (редко)
		ww.schemas.CharacterTriggerSchema(current_q='Q3', next_q='Q4', trigger_q='Q4', threshold=0.5),   # “Остывает”, если встречает полный холод, игнор или превосходство
		ww.schemas.CharacterTriggerSchema(current_q='Q3', next_q='Q1', trigger_q='Q1', threshold=0.7),   # Агрессия срывается в обиду, если другая сторона “жертвует” демонстративно
		ww.schemas.CharacterTriggerSchema(current_q='Q1', next_q='Q4', trigger_q='Q4', threshold=0.6),   # Из состояния жертвы уходит в холод и игнор, если “его страданиям нет ответа”
		ww.schemas.CharacterTriggerSchema(current_q='Q1', next_q='Q2', trigger_q='Q2', threshold=0.6),   # Если кто-то искренне заботится — может попробовать вернуться в “сотрудничество”
		ww.schemas.CharacterTriggerSchema(current_q='Q2', next_q='Q4', trigger_q='Q4', threshold=0.7),   # Попытка служить встречает игнор — становится “над ситуацией”
		ww.schemas.CharacterTriggerSchema(current_q='Q2', next_q='Q3', trigger_q='Q3', threshold=0.5),   # Попытка служить встречает агрессию — переходит в раздражённую агрессию
	]
)


character = ww.schemas.CharacterSchema.put(
	name          = 'Вася',
	descriptions  = ['умник 35 лет'],
	description   = 'умник 35 лет',
	fear          = 'боится показаться слабым',
	desire        = 'хочет быть увиденным',
	bypass        = 'раздражение и гневные действия',
	manipulation1 = 'гнев, неуваженительное обращение',
	# manipulation2 = 'слёзы',
	resource      = 'увиденность',
	trigger       = 'непринятый энтузиазм',
	voice1        = 'я офигенный и с моими чувствами стоит считаться, иначе вам будет плохо',
	# voice2        = 'я плохой и никому не нужен',
	problem       = 'страх бессилия',
	mission       = 'стать первоклассным программистом, тогда все увидят какой он классный. Так же незаметно и исподволь пытается продать свой старый тостер',
	schtick       = 'грубость речи',
	speech_style  = 'жесткий и насмешливый'
)

vasya_messages = [
	'Саша, объясни, зачем вообще нужны эти функции в коде?',
	'А нельзя просто скопировать кусок кода туда, где нужно?',
	'Понял. А если функция слишком длинная?',
	'А как функция узнает, с какими данными работать?',
	'А что возвращает функция обратно?',
	'А можно ли внутри функции вызывать другую функцию?',
]

sasha_messages = [
	'Функции помогают не повторять один и тот же код, их можно вызывать сколько угодно раз.',
	'Можно, но тогда, если нужно что-то поменять, придется править везде вручную.',
	'Значит, её можно разбить на несколько маленьких, каждая будет отвечать за свою задачу.',
	'Ты можешь передать ей аргументы — значения, с которыми она будет что-то делать.',
	'Обычно она возвращает результат своей работы через return.',
	'Да, конечно! Так строится вся логика программы: функции вызывают друг друга.',
]

vasya_stream = ww.schemas.StreamSchema.put(
	name   = 'Вася',
	role   = 'user',
	author = 'Вася'
)

sasha_stream = ww.schemas.StreamSchema.put(
	name   = 'Саша',
	role   = 'assistant',
	author = 'Саша'
)

setting = '''
	Вася находится на обучении у Саши - профессора программирования.
	Вася занимается один-на-один и платит за это немалые деньги
	так как Васе нужно пересдать экзамен, который он завалил.
'''

for v, s in zip(vasya_messages, sasha_messages):
	vasya_stream.write(v)
	sasha_stream.write(s)

class Life(ww.operators.Agent):
	agents = {
		'character' : ww.operators.life.Character,
	}

	def get_next_author(self):
		dialog_stream = ww.schemas.StreamSchema.zip(*self.state.actors)
		author = self.state.human
		if last_gulp := dialog_stream.last_gulp():
			idx    = self.state.actors.index(last_gulp.author)
			author = self.state.actors[(idx + 1) % len(self.state.actors)]
		return author

	# async def summarize(self, author, conversation, beats, length):
	# 	return await self.agents.summarizer(
	# 		author,
	# 		conversation.last(beats).to_prompt(),
	# 		length
	# 	)

	# async def get_summaries(self, author, conversation):
	# 	if len(conversation):
	# 		return {
	# 			'long'  : await self.summarize(author, conversation, -1, 'одно предложение'),
	# 			'short' : await self.summarize(author, conversation, 4, 'одно предложение'),
	# 			'last'  : conversation.last(1).to_prompt(),
	# 		}
		
	async def invoke(self, human, actors):
		streams = {
			'Вася': vasya_stream,
			'Саша': sasha_stream,
		}

		while True:
			author  = self.get_next_author()
			message = None

			# conversation = ww.schemas.StreamSchema.zip(*actors)
			
			if author == human:
				message = input(f'{human}: ')
				streams[human].write(message)
			else:
				# summaries = await self.get_summaries(author, conversation=conversation)
				message   = await self.agents.character(author, actors, setting)
				print(f'\n🤖 {author}: {message}\n')

			