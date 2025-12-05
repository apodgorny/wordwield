from wordwield.lib.o import O
from typing import Optional


class StorySchema(O):
	name      : str = O.Field(default=None, description='Краткий идентификатор или уникальное имя этой истории.')
	title     : str = O.Field(default=None, description='Полное, формальное название истории, как оно будет представлено читателям.')
	genre     : str = O.Field(default=None, description='Литературный жанр или категория истории (например, историческая драма, комедия, научная фантастика).')
	time      : str = O.Field(default=None, description='Привлизительное время действия')
	place     : str = O.Field(default=None, description='Приблизительное место действия')
	moral     : str = O.Field(default=None, description='Мораль истории, красная нить, которая накаляется, прячется и появляется снова по ходу истории, которая становится явной и неотвратимой в развязке')
	problem   : str = O.Field(default=None, description='Общая проблема или конфликт на которой сфокусированы персонажи в течение всей истории')
	plot      : str = O.Field(default=None, description='Краткое изложение основного сюжета и ключевых событий.')
	outcome   : str = O.Field(default=None, description='Финал истории, развязка, к которой всё движется. Финал должен быть глубоко удовлетворительным для читателя. Он должен быть окончательным а не prequelом')