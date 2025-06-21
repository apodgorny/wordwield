import sys, os

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_NAME = os.path.basename(PROJECT_PATH)

ROOT = os.path.join(PROJECT_PATH, '..', '..')
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from wordwield import ww

################################################################

# Initialize WordWield
ww.init(
	PROJECT_NAME = PROJECT_NAME,
	PROJECT_PATH = PROJECT_PATH,
)

# Save project schema
ww.schemas.ProjectSchema(
	name    = PROJECT_NAME,
	intent  = 'To sucsessfully complete game of guessing a number',
	description   = '''
		This is a guessing game where agents are in a dialogue.
		After guesser makes a guess, guess_approver must reply once.
		After guess_approver provides correction – it is a guesser turn again.
	''',
	manager = 'manager',
	agents  = ['manager', 'guesser', 'guess_approver'],
	streams = ['invoke_stream', 'guess_stream', 'direction_stream', 'correct_stream'],
).save()

ww.schemas.AgentSchema(
	name            = 'manager',
	class_name      = 'Manager',
	intent          = 'To choose the next agent to act, ensuring agents never act twice in a row.',
	response_schema = 'ManagerResponseSchema',
	template        = '''
		We are a {{name}} AI agent of a numer guessing game.
		Description of the game:
		----
		{{project.description}}
		----
		Your objective is {{intent}}.
		Agents:
		{% for name, intent in project.agent_intents.items() %}
		- "{{ name }}" is {{ intent.lower() }}
		{% endfor %}
		{% if project.has_history %}
			Last agent called was: {{ project.history[-1].author }}
			Agents do not reply to themselves and don't act twice in a row.
			Which agent should act next?
		{% else %}
			Since no guesses has been made yet – pick one who has to make a guess
			Which agent’s intent is to make a guess? Select that agent.
		{% endif %}
	'''
).save()

ww.schemas.AgentSchema(
	name            = 'guesser',
	class_name      = 'Developer',
	intent          = 'To generate a guess based on previous guess results in a minimal number of steps.',
	response_schema = 'DeveloperResponseSchema',
	template        = '''
		We are playing a guessing game, you are a {{name}} in the game.
		Description of the game:
		----
		{{project.description}}
		----
		Your objective is {{intent}}.
		{% if project.has_history %}
			Here is a history of guesses and guess responses:
			{% for item in project.history %}
				{{item.author}}: {{item.value}}
			{% endfor %}
		{% else %}
			No guesses has been made yet.
		{% endif %}
		Don't increase/decreas guess by one, use strategy.
		Output a whole positive number.
		Only numeric symbols, please, no quotes, ticks or other characters.
	'''
).save()

ww.schemas.AgentSchema(
	name            = 'guess_approver',
	class_name      = 'Tester',
	intent          = 'To always respond to guessed number with directions for the next guess without giving away the correct number directly',
	response_schema = 'TesterResponseSchema',
	template        = '''
		We are playing a guessing game, you are a {{name}} in the game.
		Description of the game:
		----
		{{project.description}}
		----
		Your objective is {{intent}}.
		You are thinking of a number {{project.correct_number}}.
		Guesser guessed {{project.guessed_number}}
		See if guess is correct. If it is not – nudge guesser in the right direction.
		Do not mention numbers. No numeric values must be present in your response.
		Phrase like "Try a number closer to 50." – is wrong, because it mentions a number.
	'''
).save()

ww.schemas.StreamSchema(name = 'invoke_stream',    role = 'invoke_stream', author='manager').save()
ww.schemas.StreamSchema(name = 'guess_stream',     role = 'dev_stream',    author='guesser').save()
ww.schemas.StreamSchema(name = 'direction_stream', role = 'bug_stream',    author='guess_approver').save()
ww.schemas.StreamSchema(name = 'correct_stream',   role = 'prod_stream',   author='guess_approver').save()

# Start the project operator
prod_gulps = ww(ww.operators.GuessingGame(PROJECT_NAME)(correct_number=42))
print('Correct number was guessed:', prod_gulps[-1].value)
