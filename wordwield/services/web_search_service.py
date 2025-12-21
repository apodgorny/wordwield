# ======================================================================
# Google + Scraper + RAG 
# ======================================================================

import time

from wordwield.core.base.service import Service


class WebSearchService(Service):

	# Initialize service
	# ----------------------------------------------------------------------
	def initialize(self):
		self.rag     = self.ww.services.RagService      # Vector storage and retrieval
		self.google  = self.ww.services.GoogleService   # Web discovery via Google
		self.website = self.ww.services.WebsiteService  # Page loading and text extraction
		self.cache   = self.ww.services.CacheService    # Cache

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Resolve a modification time for a search result
	# ----------------------------------------------------------------------
	def _get_mtime(self, result):
		published = result.get('date')
		if published:
			return int(published.timestamp())
		return int(time.time())
	
	# Generate deterministic rag domain name from intent
	# ----------------------------------------------------------------------
	def _get_domain_id(self, query):
		return f'web_search_{abs(hash(query))}'
	
	# Ingest web search results into a RAG domain
	# ----------------------------------------------------------------------
	def _load_docs(self, results):
		texts = {}
		for result in results:
			if result:
				url   = result.url
				title = result.title
			else:
				url   = None
				title = None
			if url:
				text = self.website.load(url, title)             # Load and extract page text
				texts[url] = text

		return texts if len(texts) else None

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Search within an existing RAG domain
	# ----------------------------------------------------------------------
	async def search(self, query, k_results=1, k_chunks=10, time_range=None):
		domain = self._get_domain_id(query)
		if not self.rag.has_domain(domain):
			if time_range is None:
				time_range = (None, None)

			docs = self.google.search(    # List of DocSchema
				query      = query,       # Search query
				time_range = time_range,  # Time constraint
				top_k      = k_results    # Result count
			)

			print(f'Googled {len(docs)} results')
			docs = await self.website.load(docs)

			for doc in docs:
				print(doc)

			self.rag.add_many(domain, docs)

		texts = self.rag.search(
			query    = query,
			domain   = domain,
			k        = k_chunks
		)
		return texts
