from sentence_transformers import CrossEncoder

from wordwield.core.base.reranker import Reranker


class CrossEncoderReranker(Reranker):

	# Init
	# ----------------------------------------------------------------------
	def __init__(self):
		self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

	# Re-rank using cross encoder
	# ----------------------------------------------------------------------
	def rerank(self, query, texts):
		rerank_scores = self.cross_encoder.predict([(query, text) for text in texts])
		return list(rerank_scores)
