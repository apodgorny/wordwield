# ======================================================================
# Expertise wrapper around Rag for folder-based knowledge.
# ======================================================================

import os

from wordwield.core.base.service import Service
from wordwield.core.fs           import Directory, File


class ExpertiseService(Service):

	# ------------------------------------------------------------------
	def initialize(self, folder=None):
		if folder is None:
			folder = self.ww.config.EXPERTISE_DIR

		self.folder       = os.path.abspath(os.path.expanduser(folder))
		self.directory    = Directory(self.folder)
		self.rag          = self.ww.services.RagService
		self.domain       = 'expertise'
		self.readable_ext = self.ww.config.EXPERTISE_FILE_EXT

		self.sync()

	# ------------------------------------------------------------------
	def sync(self):
		fs_docs = self.directory.list_files(extensions=self.readable_ext)
		print(fs_docs)
		db_docs = self.rag.get_docs(self.domain)    # { key : mtime }

		# Remove vanished files
		for key in db_docs:
			if key not in fs_docs:
				self.rag.unset(self.domain, key)

		# Add / update changed files
		for key, mtime in fs_docs.items():
			prev = db_docs.get(key)
			if prev is not None and mtime <= prev:
				continue

			text = File(key).read()
			self.rag.set(
				domain = self.domain,
				key    = key,
				text   = text,
				mtime  = int(mtime)
			)

		return None

	# ------------------------------------------------------------------
	def search(self, query, k=5):
		return self.rag.search(
			query  = query,
			domain = self.domain,
			k      = k
		)
