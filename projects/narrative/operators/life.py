from wordwield import ww
from wordwield.lib.vdb import VDB


character = ww.schemas.CharacterSchema.put(
	name          = 'Вася',
	descriptions  = ['простой хороший парень 35 лет'],
	description   = 'простой хороший парень 35 лет',
	fear          = 'боится не вписаться в общество',
	desire        = 'хочет быть нужным и любимым',
	bypass        = 'служение, по этому Вася изучает программирование',
	manipulation1 = 'служение, уваженительное обращение',
	manipulation2 = 'слёзы',
	resource      = 'нужность',
	trigger       = 'непринятый энтузиазм',
	voice1        = 'я хороший мальчик и многое могу дать',
	voice2        = 'я плохой и никому не нужен',
	problem       = 'страх общения',
	mission       = 'стать первоклассным программистом, тогда он будет нужен людям',
	schtick       = 'хороший ученик',
	speech_style  = 'заикание'
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

for v, s in zip(vasya_messages, sasha_messages):
	vasya_stream.write(v)
	sasha_stream.write(s)

class Life(ww.operators.Agent):
	agents = {
		'character'  : ww.operators.life.Character,
		'summarizer' : ww.operators.Summarizer
	}

	def get_next_author(self):
		dialog_stream = ww.schemas.StreamSchema.zip(*self.state.actors)
		author = self.state.human
		if last_gulp := dialog_stream.last_gulp():
			idx    = self.state.actors.index(last_gulp.author)
			author = self.state.actors[(idx + 1) % len(self.state.actors)]
		return author

	async def summarize(self, author, conversation, beats):
		return await self.agents.summarizer(
			author,
			conversation.last(beats).to_prompt()
		)

	async def get_summaries(self, author):
		conversation = ww.schemas.StreamSchema.zip(*self.state.actors)
		if len(conversation):
			return {
				'long'  : await self.summarize(author, conversation, -1),
				'short' : await self.summarize(author, conversation, 4),
				'last'  : await self.summarize(author, conversation, 1),
			}
		
	async def invoke(self, human, actors):
		streams = {
			'Вася': vasya_stream,
			'Саша': sasha_stream,
		}

		while True:
			author  = self.get_next_author()
			message = None

			if author == human:
				message = input(f'{human}: ')
			else:
				summaries = await self.get_summaries(author)
				message   = await self.agents.character(author, actors, summaries)
				print(f'\n🤖 {author}: {message}\n')

			streams[author].write(message)
