import chromadb
from sentence_transformers import SentenceTransformer


class VDB:
	def __init__(self, collection_name='memory', model_url='paraphrase-multilingual-MiniLM-L12-v2'):
		self.client     = chromadb.Client()
		self.collection = self.client.create_collection(collection_name)
		self.model      = SentenceTransformer(model_url)

	def to_vector(self, text):
		return self.model.encode([text])[0].tolist()

	def set(self, text, meta=None, doc_id=None):
		meta    = meta or {}
		vec     = self.to_vector(text)
		n       = len(self.collection.get()['documents'])
		doc_id  = doc_id or f'doc_{n}'

		self.collection.add(
			embeddings = [vec],
			documents  = [text],
			metadatas  = [meta],
			ids        = [doc_id],
		)
		return doc_id

	def get(self, query, n_results=5, where=None):
		vec = self.to_vector(query)
		results = self.collection.query(
			query_embeddings = [vec],
			n_results        = n_results,
			where            = where,
		)
		# Возвращаем список кортежей (текст, score, метаданные, id)
		return [
			(
				results['documents'][0][i],
				results['distances'][0][i],
				results['metadatas'][0][i],
				results['ids'][0][i]
			)
			for i in range(len(results['documents'][0]))
		]
