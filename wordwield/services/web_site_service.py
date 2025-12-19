# ======================================================================
# Web page loading and text extraction service.
# ======================================================================

import requests
import trafilatura

from tqdm import tqdm

from wordwield.core.base.service import Service


class WebSiteService(Service):
	timeout    = 20
	user_agent = 'WordWield-WebSite/1.0'

	# Initialize
	# ----------------------------------------------------------------------
	def initialize(self):
		# Explicitly set defaults for clarity; class attributes provide safe
		# fallbacks when the service is used before initialization completes.
		self.timeout    = 20
		self.user_agent = 'WordWield-WebSite/1.0'
		self.cache      = self.ww.services.CacheService

	# ======================================================================
	# PUBLIC
	# ======================================================================

	# Load raw HTML from a URL
	# ----------------------------------------------------------------------
	def load(self, url):
		cached = self.cache.get(url)
		if cached is not None:
			self.ww.log_info(f'Loading `{url}` (cache hit)')
			return cached

		self.ww.log_info(f'Loading `{url}`')
		try:
			response = requests.get(
				url,
				timeout = self.timeout,
				headers = {
					'User-Agent': self.user_agent
				}
			)
			response.raise_for_status()
		except requests.exceptions.HTTPError:
			return None

		html = response.text
		self.cache.set(url, html)
		return html

	# Extract readable text from HTML
	# ----------------------------------------------------------------------
	def extract_text(self, html):
		return trafilatura.extract(
			html,
			include_comments = False,
			include_tables   = False
		)
