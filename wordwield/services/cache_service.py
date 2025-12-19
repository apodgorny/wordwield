# ======================================================================
# Simple in-memory cache for fetched web content.
# ======================================================================

from wordwield.core.base.service import Service


class CacheService(Service):
	# Initialize cache store
	# ----------------------------------------------------------------------
	def initialize(self):
		self._store = {}

	# Retrieve cached text by key
	# ----------------------------------------------------------------------
	def get(self, key):
		return self._store.get(key)

	# Store text by key
	# ----------------------------------------------------------------------
	def set(self, key, text):
		self._store[key] = text
