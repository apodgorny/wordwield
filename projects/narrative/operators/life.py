from wordwield import ww
from wordwield.lib.vdb import VDB


class Life(ww.operators.Project):
	async def invoke(self):
		vdb = VDB()
		# 1. Заполним память разными типами событий, персонажей, reasoning-полями
		vdb.set(
			'Анна встретила Вронского на балу и почувствовала радость.',
			meta={
				'character': 'Анна',
				'type': 'действие',
				'ep': 1,
				'reasoning': 'Анна была счастлива видеть Вронского впервые за долгое время.'
			}
		)
		vdb.set(
			'Вронский наблюдал за Анной издалека и заметил, что она улыбается.',
			meta={
				'character': 'Вронский',
				'type': 'наблюдение',
				'ep': 1,
				'reasoning': 'Вронский понял, что настроение Анны улучшилось.'
			}
		)
		vdb.set(
			'Анна вспомнила прошлую ссору с мужем и ощутила тревогу.',
			meta={
				'character': 'Анна',
				'type': 'внутренний монолог',
				'ep': 2,
				'reasoning': 'Тревога вызвана мыслями о конфликте.'
			}
		)
		vdb.set(
			'Вронский подошёл к Анне и предложил ей потанцевать.',
			meta={
				'character': 'Вронский',
				'type': 'действие',
				'ep': 2,
				'reasoning': 'Вронский хочет быть ближе к Анне.'
			}
		)
		vdb.set(
			'Анна смутилась, но согласилась танцевать.',
			meta={
				'character': 'Анна',
				'type': 'действие',
				'ep': 2,
				'reasoning': 'Анна не хотела привлекать внимание, но не смогла отказать.'
			}
		)
		vdb.set(
			'Каренин заметил, что Анна исчезла с бала.',
			meta={
				'character': 'Каренин',
				'type': 'наблюдение',
				'ep': 2,
				'reasoning': 'Каренин обеспокоен поведением жены.'
			}
		)

		# 2. Запрос: Кто был обеспокоен поведением Анны?
		print('\n--- Поиск: Кто был обеспокоен поведением Анны? ---')
		for doc, dist, meta, doc_id in vdb.get(
			'Кто был обеспокоен поведением Анны?', n_results=3):
			print(f'{doc}\n  dist: {dist:.4f} | meta: {meta} | id: {doc_id}')

		# 3. Запрос: Почему Анна чувствовала тревогу?
		print('\n--- Поиск: Почему Анна чувствовала тревогу? ---')
		for doc, dist, meta, doc_id in vdb.get(
			'Почему Анна чувствовала тревогу?', n_results=3, where={'character': 'Анна'}):
			print(f'{doc}\n  dist: {dist:.4f} | meta: {meta} | id: {doc_id}')
			if 'reasoning' in meta:
				print(f'  explanation: {meta["reasoning"]}')

		# 4. Запрос: Что понял Вронский про настроение Анны?
		print('\n--- Поиск: Что понял Вронский про настроение Анны? ---')
		for doc, dist, meta, doc_id in vdb.get(
			'Что понял Вронский про настроение Анны?', n_results=3, where={'character': 'Вронский'}):
			print(f'{doc}\n  dist: {dist:.4f} | meta: {meta} | id: {doc_id}')
			if 'reasoning' in meta:
				print(f'  explanation: {meta["reasoning"]}')