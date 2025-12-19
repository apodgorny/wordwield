# ==========================================================================================
# Agent for semantic web search, ingestion, and retrieval.
# ==========================================================================================

from wordwield import ww

from wordwield.core.base import Tool


class WebSearchTool(Tool):
	intent   = 'Semantic web search and retrieval'     # Generic intent description
	verbose  = False                                   # Disable verbose output

	# ==========================================================================================
	# PRIVATE METHODS
	# ==========================================================================================

	# Generate deterministic rag domain name from intent
	# ------------------------------------------------------------------------------------------
	def _get_domain_id(self, query):
		return f'web_search_{abs(hash(query))}'

	# ==========================================================================================
	# PUBLIC METHODS
	# ==========================================================================================

	# Perform semantic web search and return relevant chunks
	# ------------------------------------------------------------------------------------------
	async def invoke(self,
		query            : str,                      # User-provided search query or intent text
		k_results        : int              = 5,     # Amount of results to consider
		k_chunks         : int              = 10,    # Amount of relevant chunks from results
		time_range       : tuple[int, int]  = None   # (from_ts, to_ts) unix timestamps
	) -> list[str]:
		
		domain = self._get_domain_id(query)

		relevant_chunks = ww.services.WebSearchService.search(
			query     = query,
			domain    = domain,
			k_results = k_results,
			k_chunks  = k_chunks
		)

		return relevant_chunks
