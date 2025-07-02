from wordwield import ww


class Spirit(ww.operators.Unfolder):
	streams = ['stream']

	questions = [
		'В чем суть происходящего?',
		'Что я должен сделать?',
		'Какие варианты действий есть в моём распоряжении выполнить мою миссию? Список где каждый элемент 2-3 слова.',
		'Какои вариант поведения я выберу, чтобы всё улучшить? Выбираю только один из моего списка выше. 2-3 слова',
		'''
			Конкретное физическое действие. (Не длиннее одного предложения, в настоящем времени.)
			ВСЕГДА: отвечай как «от автора», описывая происходящее в третьем лице. Используй конструкции вроде 
			«Происходит ...», «Персонаж обнаруживает ...», «Погода становится ...»,
			НИКОГДА: не давай прямых указаний персонажам, а только констатируй новые обстоятельства и изменения в мире.
		'''
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
				{{ gulp.author }}: «{{ gulp.value }}»
			{% endfor %}
			--------------------
		{% endif %}

		--------------------
		{{unfoldment}}
		--------------------

		{{question}}
	'''

	async def invoke(self, character_name, history):
		self.state.character = ww.schemas.CharacterSchema.get(character_name)
		result = await super().invoke()
		self.streams.stream.write(result, author=character_name)
		return result
