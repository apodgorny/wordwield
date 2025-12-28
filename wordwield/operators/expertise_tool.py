# ======================================================================
# Agent for semantic web search, ingestion, and retrieval.
# ======================================================================

from wordwield import ww

from wordwield.core.base import Tool


class ExpertiseTool(Tool):
	intent   = 'Semantic expertise search and retrieval'  # Generic intent description
	verbose  = False                                      # Disable verbose output

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform semantic web search and return relevant chunks
	# ----------------------------------------------------------------------
	async def invoke(self,
		query : str,                      # User-provided search query or intent text
		top_k : int
	) -> list[str]:
		
		items = await ww.services.ExpertiseService.search(
			query = query,
			top_k = top_k
		)

		return items
