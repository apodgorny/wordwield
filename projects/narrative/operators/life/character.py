from wordwield     import ww
from wordwield.core import O


class Character(ww.operators.Agent):
	verbose      = True
	conversation = None

	agents = {
		'summarizer' : ww.operators.life.Summarizer,
		'analyzer'   : ww.operators.life.QuadrantAnalyzer,
		'corrector'  : ww.operators.life.Corrector
	}

	class ResponseSchema(O):
		reply   : str = O.Field(description='Прямая речь от первого лица обращенная к говорившему персонажу - ответ на предыдущее событие или встречный вопрос. ТОЛЬКО голос твоего персонажа. НЕ БОЛЕЕ ДВУХ ПРЕДЛОЖЕНИЙ. Связно и членораздельно')
		comment : str = O.Field(description='Всё кроме прямой речи пиши сюда. Максимум одно предложение.')

	template = '''
		Ты - живой персонаж {{ character.name }}
		Вот суть ситуации:
		{{ setting }}
		Твоё эмоциональное состояние:
		-------------------
		{{ quadrant }}
		-------------------
		Роли участников:
		{{ summary['roles'] }}
		Было вот что
		{{ summary['interaction'] }}
		A потом:
		{{ summary['events'] }}
		И вот только что:
		{{ last_beats }}
		Ответь обращаясь к персонажу {{ opponent }}. Среагируй на ситуацию в соответствии со своим эмоциональным состоянием.
		Если нужно - задай вопрос.
		'''
	
	async def analyze_last_beat(self, author, conversation):
		dialogue = conversation.to_prompt()
		last_phrase = conversation.last(1).to_prompt()
		print('*'*100)
		print('*'*100)
		print('Analyzing author:', author)
		print('Analyzing:', conversation.last(1).to_prompt())
		analysis = await self.agents.analyzer(
			name        = author,
			dialogue    = dialogue,
			last_phrase = last_phrase,
			unpack      = False
		)
		print(conversation.to_prompt())
		print(analysis)
		print('*'*100)
		print('*'*100)

	async def invoke(self, name, actors, setting):
		conversation = ww.schemas.StreamSchema.zip(*actors)
		self.state.quadrant  = ww.schemas.QuadrantSchema().Q2
		self.state.character = ww.schemas.CharacterSchema.get(name)
		self.state.summary   = await self.agents.summarizer(name, conversation.to_prompt())
		
		self.state.last_beats = conversation.since_last_author(name).to_prompt()
		self.state.opponent   = conversation.last(1).gulps[0].author

		reply, _ = await super().invoke()  # Garbage collector pattern
		reply    = await self.agents.corrector(reply)

		ww.schemas.StreamSchema.get(name).write(reply)
		conversation = ww.schemas.StreamSchema.zip(*actors)
		await self.analyze_last_beat(name, conversation)

		return reply
