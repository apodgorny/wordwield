from wordwield import ww


class Character(ww.operators.Unfolder):
	streams = ['stream']

	questions = [
		'В чем суть происходящего?',
		'Что хорошего я вижу в происходящем? (Не длиннее одного предложения)',
		'Что можно улучшить в моей ситуации? (Не длиннее одного предложения)',
		'Какие варианты действий есть в моём распоряжении чтобы всё улучшить? Список где каждый элемент 2-3 слова.',
		'Какои вариант поведения я выберу, чтобы всё улучшить? Выбираю только один из моего списка выше. 2-3 слова',
		'Конкретное физическое действие. (Не длиннее одного предложения, в настоящем времени. Пример: я иду, я делаю или я начинаю)'
	]
	template = '''
		Я {{character.name}}.
		Обо мне:
		--------------------
		{{character}}
		--------------------

		{% if history %}
			Вот запись произошедьшего:
			--------------------
			{% for gulp in history %}
				[{{ gulp.author }}]: «{{ gulp.value }}»
			{% endfor %}
			--------------------
		{% endif %}

		--------------------
		{{unfoldment}}
		--------------------

		{{question}}

		Отвечай от первого лица "Я ..."
	'''

	async def invoke(self, character_name, history):
		self.state.character = ww.schemas.CharacterSchema.get(character_name)
		result = await super().invoke()
		self.streams.stream.write(result, author=character_name)
		return result
