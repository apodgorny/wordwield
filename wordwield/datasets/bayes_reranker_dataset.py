import re

from wordwield import ww


class BayesRerankerDataset:

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Split extracted text into chunks suitable for Bayes prior.
	# ----------------------------------------------------------------------
	def _split_chunks(self, text):
		lines = []

		if text:
			for block in text.split('\n'):
				block = block.strip()
				if block:
					lines.append(block)

		return lines

	# Weak supervision: 1 = content, 0 = noise
	# ----------------------------------------------------------------------
	def _auto_label(self, chunk):
		l      = len(chunk)
		tokens = chunk.split()

		# Very short → noise
		if l < 30 or len(tokens) < 5:
			return 0

		# Obvious navigation / CTA patterns
		if re.search(r'(subscribe|sign up|log in|sign in|privacy policy|cookie)', chunk, re.I):
			return 0

		# All caps short lines → headers / noise
		if chunk.isupper() and len(tokens) < 10:
			return 0

		# Lists of links / bullets
		if re.match(r'^(\d+\.|-|\*)\s+', chunk):
			return 0

		# Otherwise assume content
		return 1

	# ----------------------------------------------------------------------
	def _load_page_chunks(self, url):
		html = ww.services.WebsiteService.load(url)
		text = ww.services.WebsiteService.extract_text(html)

		return self._split_chunks(text) if text else []

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# urls: list[str], max_pages: optional limit, returns: (texts, labels)
	# ----------------------------------------------------------------------
	def load(self, urls):
		texts  = []
		labels = []
		count  = 0

		for url in urls:
			chunks = self._load_page_chunks(url)

			for chunk in chunks:
				texts.append(chunk)
				labels.append(self._auto_label(chunk))

			count += 1

		return texts, labels
