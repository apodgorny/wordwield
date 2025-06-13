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
							varname = 'history',
							streams = ['numbers', 'comments'],
							length  = -1
						)
					],
					write = [
						VariableSchema(
							varname = 'guessed_number',
							streams = ['numbers']
						)
					],
					template = '''
						{% if history %}
							History of previous guesses:
							{{ history }}
							Based on guess history try to provide a better number guess.
						{% else %}
							Guess a number between 0 and 100
						{% endif %}
						Only output a number, nothing else, please. e.g: 42, 1, 3
					''',
					response_type = 'NumberSchema'
				),
				AgentSelectorSchema(
					name = 'corrector',
					type = 'selector',
					read = [
						VariableSchema(
							varname = 'guessed_number',
							streams = ['numbers'],
							length  = 1
						),
						VariableSchema(
							varname = 'correct_number',
							streams = ['source'],
							length  = 1
						)
					],
					write_true = [
						VariableSchema(
							varname = 'comment',
							streams = ['comments']
						),
					],
					write_false = [
						VariableSchema(
							varname = 'guessed_number',
							streams = ['target']
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
		return f'You guessed: {result}'
