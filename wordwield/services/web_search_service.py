# ======================================================================
# Google + Scraper + RAG 
# ======================================================================

import time

from wordwield.core.base.service import Service


class WebSearchService(Service):

	# Initialize service
	# ----------------------------------------------------------------------
	def initialize(self):
		self.rag             = self.ww.services.RagService      # Vector storage and retrieval
		self.google          = self.ww.services.GoogleService   # Web discovery via Google
		self.website_service = self.ww.services.WebSiteService  # Page loading and text extraction

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Load web page and extract readable text
	# ----------------------------------------------------------------------
	def _get_text(self, webpage):
		text = None
		html = self.website_service.load(
			url = webpage['url']                             # Page URL
		)
		if html:
			text = self.website_service.extract_text(
				html = html                                        # Raw HTML content
			)
		return text

	# Resolve a modification time for a search result
	# ----------------------------------------------------------------------
	def _get_mtime(self, result):
		published = result.get('date')
		if published:
			return int(published.timestamp())
		return int(time.time())
	
	# Ingest web search results into a RAG domain
	# ----------------------------------------------------------------------
	def _ingest(self, query, time_range, domain, k_results):
		results = self.google.search(
			query      = query,       # Search query
			time_range = time_range,  # Time constraint
			top_k      = k_results    # Result count
		)

		for result in results:
			text = self._get_text(result)               # Load and extract page text
			key  = result.get('url') if result else None
			if text and key:
				self.rag.add(
					domain         = domain,            # Target RAG domain
					key            = key,               # Use URL as unique key
					text           = text,              # Extracted content
					external_mtime = self._get_mtime(result)
				)

		self.ww.db.commit()

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Search within an existing RAG domain
	# ----------------------------------------------------------------------
	def search(self, query, domain, k_results=1, k_chunks=10, time_range=None):
		if not self.rag.has_domain(domain):
			if time_range is None:
				time_range = (None, None)
				
			self._ingest(
				query      = query,
				domain     = domain,
				time_range = time_range,
				k_results  = k_results
			)

		texts = self.rag.search(
			query    = query,
			domain   = domain,
			k        = k_chunks
		)
		return texts
