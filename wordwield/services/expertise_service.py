# ======================================================================
# Expertise wrapper around Rag for folder-based knowledge.
# ======================================================================

import os

from wordwield.core.base.service import Service
from wordwield.core.db           import RagDocument
from wordwield.core.fs           import Directory, File


class ExpertiseService(Service):
	def initialize(self, folder=None):
		if folder is None:
			folder = self.ww.config.EXPERTISE_DIR

		self.folder       = os.path.abspath(os.path.expanduser(folder))
		self.directory    = Directory(self.folder)
		self.rag          = self.ww.services.RagService
		self.domain       = 'expertise'
		self.readable_ext = self.ww.config.get('EXPERTISE_FILE_EXT', {'txt', 'md', 'docx', 'html', 'htm', 'pdf'})

		self.sync()

	# Sync folder contents into the expertise domain
	# ----------------------------------------------------------------------
	def sync(self):
		fs_doc_paths = self.directory.list_files(extensions=self.readable_ext)
		db_docs      = RagDocument.get_by_domain(self.domain)
		db_doc_paths = {doc.key for doc in db_docs}
		db_mtimes    = {doc.key: doc.mtime for doc in db_docs}

		# Remove missing files
		missing_paths = [path for path in db_doc_paths if path not in fs_doc_paths]
		if missing_paths:
			for path in missing_paths:
				print(f'Removed missing file from Expertise: `{path}`')
			self.rag.remove(self.domain, missing_paths)

		# Add/update current files
		for path, mtime in fs_doc_paths.items():
			text = File(path).read()
			self.rag.add(self.domain, path, text, int(mtime))

		self.ww.db.commit()
		return None

	# Query expertise domain
	# ----------------------------------------------------------------------
	def search(self, query, k=5, ap_prev=None, keys=None, karma=0.5):
		texts, ap_next = self.rag.search(
			domain  = self.domain,
			query   = query,
			keys    = keys,
			k       = k,
			ap_prev = ap_prev,
			karma   = karma
		)
		return texts, ap_next
