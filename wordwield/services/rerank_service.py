# ======================================================================
# Service that routes queries through configured re-rankers.
# ======================================================================

from wordwield.core.base.service import Service
from wordwield.plugins.rerankers import BayesReranker, CrossEncoderReranker, LateInteractionReranker


class RerankService(Service):
	CROSS_ENCODER    = CrossEncoderReranker
	LATE_INTERACTION = LateInteractionReranker
	BAYES            = BayesReranker

	# Service initialization
	# ----------------------------------------------------------------------
	def initialize(self):
		self._instances = {}

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Select reranker instance by name
	# ----------------------------------------------------------------------
	def _get_reranker(self, reranker_class):
		if reranker_class not in self._instances:
			self._instances[reranker_class] = reranker_class()

		return self._instances[reranker_class]

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Re-rank results using configured reranker
	# ----------------------------------------------------------------------
	def rerank(self, query, texts, reranker_class=None):
		results = texts
		
		if texts:
			reranker = self._get_reranker(reranker_class)
			results  = reranker.rerank(query, texts)

		return results
