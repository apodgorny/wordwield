# ======================================================================
# BM25 relevance scoring over an in-memory document set.
# ======================================================================

from rank_bm25                    import BM25Okapi

from wordwield.core.base.service import Service


class DocumentRelevanceService(Service):

	def initialize(self):
		return None

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Rank documents for a query
	# ----------------------------------------------------------------------
	def rank(self, query, documents):
		keys              = list(documents.keys())
		tokenized_corpus  = [(documents[k] or '').split() for k in keys]
		tokenized_query   = (query or '').split()

		bm25   = BM25Okapi(tokenized_corpus)
		scores = bm25.get_scores(tokenized_query)

		results = list(zip(keys, scores))
		results.sort(key=lambda pair: pair[1], reverse=True)
		return results
