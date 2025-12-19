import math
import re
import os

import torch
from sklearn.naive_bayes import GaussianNB
from tqdm                import tqdm

from wordwield           import ww
from wordwield.core.base import Reranker
from wordwield.datasets  import BayesRerankerDataset


 # Hardcoded, genre-diverse, stable URLs
 # ----------------------------------------------------------------------
FIT_URLS = [
	# cooking / recipes
	'https://www.theclevercarrot.com/2014/01/sourdough-bread-a-beginners-guide/',
	'https://www.allrecipes.com/article/how-to-make-sourdough-bread/',
	'https://www.theperfectloaf.com/beginners-sourdough-bread/',

	# technical writing
	'https://docs.python.org/3/tutorial/introduction.html',
	'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction',

	# blogs / essays
	'https://waitbutwhy.com/2015/01/artificial-intelligence-revolution-1.html',
	'https://paulgraham.com/startupideas.html',

	# wikipedia-like reference
	'https://en.wikipedia.org/wiki/Bread',
	'https://en.wikipedia.org/wiki/Artificial_intelligence'
]

TRAINED_FILE_PATH = os.path.join(ww.config.WW_PATH, 'trained/bayes_reranker.pt')


class BayesReranker(Reranker):

	# Init
	# ----------------------------------------------------------------------
	def __init__(self):
		self._model     = GaussianNB()
		self._is_fitted = False

		self.load()

		if not self._is_fitted:
			self.fit()

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# ----------------------------------------------------------------------
	def _len_chars(self, text):
		return float(len(text))

	# ----------------------------------------------------------------------
	def _len_tokens(self, text):
		tokens = text.split()
		return float(len(tokens))

	# ----------------------------------------------------------------------
	def _token_entropy(self, text):
		tokens = text.split()
		if not tokens:
			return 0.0

		freq = {}
		for t in tokens:
			freq[t] = freq.get(t, 0) + 1

		total = len(tokens)
		entropy = 0.0

		for c in freq.values():
			p = c / total
			entropy -= p * math.log(p + 1e-12)

		return float(entropy)

	# ----------------------------------------------------------------------
	def _avg_token_length(self, text):
		tokens = text.split()
		if not tokens:
			return 0.0

		total = sum(len(t) for t in tokens)
		return float(total / len(tokens))

	# ----------------------------------------------------------------------
	def _is_header(self, text):
		if not text:
			return 0.0

		if text.strip().endswith(':'):
			return 1.0

		if text.strip().isupper():
			return 1.0

		if len(text.split()) <= 6:
			return 1.0

		return 0.0

	# ----------------------------------------------------------------------
	def _is_list(self, text):
		lines = text.strip().splitlines()
		if not lines:
			return 0.0

		matches = 0
		for l in lines:
			if re.match(r'^(\d+\.|-|\*)\s+', l.strip()):
				matches += 1

		return float(matches / len(lines))

	# ----------------------------------------------------------------------
	def _position_norm(self, index, total):
		if total <= 1:
			return 0.0

		return float(index / (total - 1))

	# ----------------------------------------------------------------------
	def _punctuation_ratio(self, text):
		if not text:
			return 0.0

		punct = sum(1 for c in text if c in '.,;:!?')
		return float(punct / len(text))

	# ----------------------------------------------------------------------
	def _digit_ratio(self, text):
		if not text:
			return 0.0

		digits = sum(1 for c in text if c.isdigit())
		return float(digits / len(text))

	# ----------------------------------------------------------------------
	def _uppercase_ratio(self, text):
		if not text:
			return 0.0

		upper = sum(1 for c in text if c.isupper())
		return float(upper / len(text))


	# Extract features
	# ----------------------------------------------------------------------
	def _extract_features(self, text, index, total):
		features = [
			self._len_chars(text),
			self._len_tokens(text),
			self._token_entropy(text),
			self._avg_token_length(text),
			self._is_header(text),
			self._is_list(text),
			self._position_norm(index, total),
			self._punctuation_ratio(text),
			self._digit_ratio(text),
			self._uppercase_ratio(text)
		]
		return features

	# 
	# ----------------------------------------------------------------------
	def _p_content(self, text, index, total):
		features = self._extract_features(text, index, total)
		proba = self._model.predict_proba([features])[0][1]
		return float(proba)

	# ======================================================================
	# PUBLIC
	# ======================================================================

	# texts: list[str], labels: list[int], (1 = content, 0 = noise)
	# ----------------------------------------------------------------------
	def fit(self, save_path=TRAINED_FILE_PATH):
		dataset       = BayesRerankerDataset()
		texts, labels = dataset.load(FIT_URLS)

		if not texts:
			raise RuntimeError('BayesRerankerDataset returned empty dataset')
		
		X = []
		y = labels

		total = len(texts)
		for i, text in tqdm(enumerate(texts), desc='Fitting Bayes Filter'):
			X.append(self._extract_features(text, i, total))

		self._model.fit(X, y)
		self._is_fitted = True

		if save_path:
			self.save(save_path)

		return self

	# Save filter .pt file to path
	# ----------------------------------------------------------------------
	def save(self, path):
		state = {
			'model'     : self._model,
			'is_fitted' : self._is_fitted
		}

		os.makedirs(os.path.dirname(path), exist_ok=True)
		ww.log_info(f'Saving BayesReranker to `{path}`')
		torch.save(state, path)

		return self

	# Load .pt file from path
	# ----------------------------------------------------------------------
	def load(self, path=None):
		path            = path or TRAINED_FILE_PATH
		state           = torch.load(path, map_location='cpu', weights_only=False)
		self._model     = state['model']
		self._is_fitted = state['is_fitted']

		return self

	# Re-rank, return list of scores in order of results
	# ----------------------------------------------------------------------
	def rerank(self, query, texts):
		if not self._is_fitted:
			self.fit()

		histogram = []

		for i, text in enumerate(texts):
			histogram.append(self._p_content(text, i, len(texts)))

		return histogram
