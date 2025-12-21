# ======================================================================
# Simple on-disk cache for fetched web content.
# ======================================================================

import os
import json
import hashlib

from wordwield.core.base.service import Service
from wordwield.core.fs           import File


class CacheService(Service):
	# Initialize cache store
	# ----------------------------------------------------------------------
	def initialize(self):
		self.cache_dir = self.ww.config.CACHE_DIR
		os.makedirs(self.cache_dir, exist_ok=True)

	# Get path of md5.cache file
	# ----------------------------------------------------------------------
	def _get_path(self, key):
		digest = hashlib.md5(key.encode('utf-8')).hexdigest()
		return os.path.join(self.cache_dir, f'{digest}.cache')

	# Retrieve cached text by key
	# ----------------------------------------------------------------------
	def get(self, key):
		text = None
		path = self._get_path(key)
		return File.read(path)

	# Store text by key
	# ----------------------------------------------------------------------
	def set(self, key, text):
		path = self._get_path(key)
		return File.write(path, text)
	
	# Decorate cacheble method
	# ----------------------------------------------------------------------
	def cache(self, retriever, **kwargs):
		key    = json.dumps(kwargs)
		data   = self.get(key)

		if not data:
			data = retriever(**kwargs)
			print('Saving to cache')
			data = json.dumps(data, ensure_ascii=False, indent=4)
			self.set(key, data)
		else:
			data = json.loads(data)
			print('Loaded from cache')

		return data

