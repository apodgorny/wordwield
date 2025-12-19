# ======================================================================
# Google search service (discovery only).
# ======================================================================

import requests

from datetime import datetime

from wordwield.core.base.service import Service


class GoogleService(Service):

	# Service initialization
	# ----------------------------------------------------------------------
	def initialize(self):
		self.google_api_key   = self.ww.env.GOOGLE_API_KEY
		self.search_engine_id = self.ww.env.GOOGLE_SEARCH_ENGINE_ID
		self.timeout          = 20

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Parse common ISO8601-ish datetime strings from metatags
	# ----------------------------------------------------------------------
	def _parse_date(self, date_str):
		if not date_str:
			return None

		candidates = [
			date_str,
			date_str.replace('Z', '+00:00')
		]

		for candidate in candidates:
			try:
				return datetime.fromisoformat(candidate)
			except Exception:
				continue

		return None

	# Convert unix timestamp to UTC datetime
	# ----------------------------------------------------------------------
	def _to_datetime(self, ts):
		result = None
		if ts is not None:
			result = datetime.utcfromtimestamp(ts)
		return result

	# Extract publication date from search item
	# ----------------------------------------------------------------------
	def _publish_date(self, item):
		result = None
		meta   = item.get('pagemap', {}).get('metatags', [])

		for tag in meta:
			for key in (
				'article:published_time',
				'article:modified_time',
				'og:updated_time',
				'datepublished',
				'pubdate'
			):
				result = self._parse_date(tag.get(key))
				if result:
					return result

		return result

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform a Google search
	# ----------------------------------------------------------------------
	def search(self, query, time_range, top_k):
		if not self.google_api_key or not self.search_engine_id:
			raise RuntimeError('Google search credentials are not configured.')

		google_api_url = 'https://www.googleapis.com/customsearch/v1'
		from_ts, to_ts = time_range                                     # Unix timestamps
		from_dt        = self._to_datetime(from_ts)
		to_dt          = self._to_datetime(to_ts)

		params = {
			'key' : self.google_api_key,
			'cx'  : self.search_engine_id,
			'q'   : query,
			'num' : min(top_k, 10)
		}

		self.log(f'Searching `{query}` ...')
		response = requests.get(
			google_api_url,
			params  = params,
			timeout = self.timeout
		)

		response.raise_for_status()

		data    = response.json()
		items   = data.get('items', [])
		results = []

		for item in items:
			link       = item.get('link')
			published  = self._publish_date(item)
			too_old    = from_dt and published and published < from_dt
			too_recent = to_dt   and published and published > to_dt

			is_valid = bool(link)

			if too_old or too_recent:
				is_valid = False

			if is_valid:
				results.append({
					'url'     : link,
					'title'   : item.get('title'),
					'snippet' : item.get('snippet'),
					'date'    : published
				})

		self.log(f'Found {len(results)} results')
		return results
