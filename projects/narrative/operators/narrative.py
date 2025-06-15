from wordwield.lib import O, Operator


class Narrative(Operator):
	def create(self, name):
		# project = ProjectSchema(
		# 	name   = name,
		# 	agents = [
		# 		ExpertSchema(
		# 			name = 'guesser',
		# 			mode = 'unary',
		# 			read = [
		# 				VariableSchema(
		# 					varname = 'history',
		# 					streams = ['numbers', 'comments'],
		# 					length  = -1
		# 				)
		# 			],
		# 			write = [
		# 				VariableSchema(
		# 					varname = 'guessed_number',
		# 					streams = ['numbers']
		# 				)
		# 			],
		# 			template = '''
		# 				{% if history %}
		# 					History of previous guesses:
		# 					{{ history }}
		# 					Based on guess history try to provide a better number guess.
		# 				{% else %}
		# 					Guess a number between 0 and 100
		# 				{% endif %}
		# 				Only output a number, nothing else, please. e.g: 42, 1, 3
		# 			''',
		# 			response_type = 'NumberSchema'
		# 		),
		# 		ExpertSchema(
		# 			name = 'corrector',
		# 			mode = 'binary',
		# 			read = [
		# 				VariableSchema(
		# 					varname = 'guessed_numbers',
		# 					streams = ['numbers'],
		# 					length  = 1
		# 				),
		# 				VariableSchema(
		# 					varname = 'correct_numbers',
		# 					streams = ['source'],
		# 					length  = 1
		# 				)
		# 			],
		# 			write_true = [
		# 				VariableSchema(
		# 					varname = 'correct_numbers',
		# 					streams = ['target']
		# 				)
		# 			],
		# 			write_false = [
		# 				VariableSchema(
		# 					varname = 'comment',
		# 					streams = ['comments']
		# 				),
		# 			],
		# 			template = '''
		# 				You are playing a guessing game
		# 				Guesser said: {{ guessed_numbers[0] }}.
		# 				The correct number he should eventually guess is {{ correct_numbers[0] }}.
		# 				Check if number was guessed correctly.
		# 				If not, provide one sentence comment to guesser to nudge him in right direction,
		# 				without giving away the correct number.
		# 				If number is correct, say: it is correct.
		# 			''',
		# 			response_type = 'SelectorSchema'
		# 		)
		# 	],
		# 	streams = [
		# 		StreamSchema(name = 'target'),
		# 		StreamSchema(name = 'source'),
		# 		StreamSchema(
		# 			name     = 'numbers',
		# 			triggers = 'corrector'
		# 		),
		# 		StreamSchema(
		# 			name     = 'comments',
		# 			triggers = 'guesser'
		# 		),
		# 	]
		# ).save()
		# return project
		...