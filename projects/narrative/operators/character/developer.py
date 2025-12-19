from wordwield.core import O, Operator, String
from wordwield     import ww


class Developer(ww.operators.Filler):
	intent     = 'раскрыть внутренний мир персонажа'
	template   = '''
		Ты — психолог, который помогает писать рассказ.
		Вот что ты знаешь про психологию:
		НАЧАЛО ЭКСПЕРТИЗЫ
		-------------------------------
		{{ww.expertise.psychologist}}
		-------------------------------
		КОНЕЦ ЭКСПЕРТИЗЫ

		Твоя цель — {{intent}}

		Вот что известно о персонаже:
		----------------------------
		{% for k, v in filled_fields.items() %}
		- {{ k }}: "{{ v }}"
		{% endfor %}
		----------------------------
		
		Опиши {{ next_field['name'] }} для персонажа — {{ next_field['description'] }}
	'''