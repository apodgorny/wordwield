from wordwield import ww


class Planner(ww.operators.Filler):
	intent     = 'создать захватывающую историю'
	template   = '''
		Ты — писатель, который планирует историю.
		Твоя цель — {{intent}}

		{% for k, v in filled_fields.items() %}
		- {{ k }}: "{{ v }}"
		{% endfor %}

		Придумай {{ next_field['name'] }} для истории — {{ next_field['description'] }}
	'''
