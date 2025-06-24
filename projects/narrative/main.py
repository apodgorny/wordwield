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
	reset_db     = False
)

ww.schemas.ProjectSchema.create_or_update(
	name        = PROJECT_NAME,
	intent      = 'Создать захватывающий нарратив',
	description = '',
	agents      = [
		'planner',
		'character_name_extractor',
		'character_description_extractor'
	],
	streams = [],
)

ww.schemas.AgentSchema.create_or_update(
	name       = 'planner',
	class_name = 'Filler',
	intent     = 'создать захватывающую историю',
	template   = '''
		Ты — писатель, который планирует историю.
		Твоя цель — {{intent}}

		{% for k, v in filled_fields.items() %}
		- {{ k }}: "{{ v }}"
		{% endfor %}

		Придумай {{ next_field['name'] }} для истории — {{ next_field['description'] }}
	'''
)

ww.schemas.AgentSchema.create_or_update(
	name       = 'character_name_extractor',
	class_name = 'Extractor',
	intent     = 'Екстрагировать персонажа из текста',
	template   = '''
		Ты — писатель, который организует персонажей из текста.
		Твоя цель — {{intent}}

		{% if names %}
			Персонажи из предыдущих глав:
			-----------
			{% for name in names: %}
			– {{name}}
			{% endfor %}
			-----------
		{% endif %}

		Перечисли персонажей упомянутых в тексте.
		Убедись, что персонаж это не название местности, города и не группа людей.
		Например "местные жители" или названия городов, титулов, рода деятельности или предметов - неверно.
		Персонажи - ТОЛЬКО ИМЕНА СОБСТВЕННЫЕ
		Перечисли ТОЛЬКО тех персонажей, которые упомянаются в следующем Тексте.

		Текст:
		-----------
		{{text}}
		-----------
	'''
)

ww.schemas.AgentSchema.create_or_update(
	name       = 'character_description_extractor',
	class_name = 'Extractor',
	intent     = 'Екстрагировать из текста описание характеризующее персонажа',
	template   = '''
		Ты — писатель, который организует персонажей из текста.
		Твоя цель — {{intent}}

		Имя персонажа: {{character_name}}

		Текст:
		-----------
		{{text}}
		-----------
		
		Выдели из текста отрывки характеризующие или описывающие персонажа {{character_name}}.
		На основе каждого отрывка дай короткую (3-7 слов) характеристику особенности персонажа, психологию, внешний вид, род занятий, пол, возраст.
	'''
)

ww.schemas.StorySchema.create_or_update(
	name  = PROJECT_NAME,
	title = 'Мухамор',
	genre = 'комедия'
)


ww(ww.operators.Narrative(PROJECT_NAME)())
