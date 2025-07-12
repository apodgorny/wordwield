from wordwield import ww


class Planner(ww.operators.Filler):
	intent     = 'создать захватывающую сцену, в которой раскрыты персонажи'
	template   = '''
		Ты — писатель, который планирует сцену.
		Твоя цель — {{intent}}

		Общая идея истории:
		-----------------------
		{{ story.plot }}
		-----------------------

		{% if previous_scene %}
			Предыдущая сцена:
			-----------------------
			{{ previous_scene }}
			-----------------------
		{% endif %}

		Вот что уже разработано о текущей сцене:
		-----------------------
		{% for k, v in filled_fields.items() %}
		- {{ k }}: "{{ v }}"
		{% endfor %}
		-----------------------

		Создай {{ next_field['name'] }} для сцены — {{ next_field['description'] }}
	'''
