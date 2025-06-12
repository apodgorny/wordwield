from wordwield.lib import O, Agent, Operator

from schemas.schemas import (
	TimelineSchema,
	AgentSchema,
	AgentSelectorSchema,
	StreamSchema,
	VariableSchema,
	BeatSchema
)

from .emitter  import Emitter
from .selector import Selector
from .stream_write import StreamWrite
from .stream_read import StreamRead


class Timeline(Operator):
	class InputType(O):
		name   : str
		number : int

	class OutputType(O):
		text: str

	def create(self, name):
		timeline = TimelineSchema(
			name   = name,
			agents = [
				AgentSchema(
					name = 'guesser',
					type = 'emitter',
					read = [
						VariableSchema(
							name    = 'history',
							threads = ['numbers', 'comments'],
							length  = -1
						)
					],
					write = [
						VariableSchema(
							name    = 'guessed_number',
							threads = ['numbers']
						)
					],
					template = '''
						Guess history:
						{history}.
						Based on guess history try to guess a number.
					''',
					response_type = 'NumberSchema'
				),
				AgentSelectorSchema(
					name = 'corrector',
					type = 'selector',
					read = [
						VariableSchema(
							name    = 'guessed_number',
							threads = ['numbers'],
							length  = 1
						),
						VariableSchema(
							name    = 'correct_number',
							threads = ['source'],
							length  = 1
						)
					],
					write_true = [
						VariableSchema(
							name    = 'comment',
							threads = ['comments']
						),
					],
					write_false = [
						VariableSchema(
							name    = 'guessed_number',
							threads = ['target']
						)
					],
					template = '''
						Guessed number is {guessed_number}.
						The correct number is {correct_number}.
						Check if number was guessed correctly.
						If not, provide one sentence directions to guesser to nudge him in right direction,
						without giving away correct number.
						If number is correct, say: it is correct.
					''',
					response_type = 'SelectorSchema'
				)
			],
			streams = [
				StreamSchema(name = 'target'),
				StreamSchema(name = 'source'),
				StreamSchema(
					name     = 'numbers',
					triggers = 'corrector'
				),
				StreamSchema(
					name     = 'comments',
					triggers = 'guesser'
				),
			]
		).save()
		return timeline

	async def invoke(self, name, number):
		timeline = TimelineSchema.load(name) or self.create(name)
		await stream_write(['source'], BeatSchema(text=str(number)))
		start_agent  = timeline.agents[0]
		await self.call(
			start_agent.type,
			name = start_agent.name
		)
		result = await stream_read('target')
		return f'You guessed: {result[0]}'
