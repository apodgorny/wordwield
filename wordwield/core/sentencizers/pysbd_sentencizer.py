#==================================================
# Sentence segmentation utility with PySBD (multilingual).
#==================================================

import pysbd
from langdetect import detect, DetectorFactory
from tqdm import tqdm

DetectorFactory.seed = 0


class PysbdSentencizer:
	# Initialize auto-language setup
	#--------------------------------------------------
	def __init__(self):
		self.supported = {
			'ar', 'hy', 'de', 'fa', 'pl', 'fr', 'am', 'zh', 'kk', 'it', 'ja',
			'mr', 'nl', 'da', 'en', 'ru', 'sk', 'hi', 'ur', 'bg', 'es', 'my', 'el'
		}

	# Convert text to sentences
	#--------------------------------------------------
	def to_sentences(self, text):
		lines = [line.strip() for line in text.splitlines() if line.strip()]

		try    : lang = detect(text)
		except : lang = 'en'

		if lang not in self.supported:
			lang = 'en'

		segmenter = pysbd.Segmenter(language=lang, clean=False)

		chunk_size = 200_000
		parts      = []
		for line in lines:
			parts.extend([line[i:i + chunk_size] for i in range(0, len(line), chunk_size)])

		sents = []
		for part in parts:
			out = segmenter.segment(part)
			for st in out:
				strip = st.strip()
				if strip:
					sents.append(strip)

		return sents
