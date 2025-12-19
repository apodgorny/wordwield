#==================================================
#Sentence segmentation utility with spaCy pipeline.
#==================================================

from spacy.lang.en import English
from tqdm          import tqdm


class SpacySentencizer:
	# Initialize spaCy pipeline
	#--------------------------------------------------
	def __init__(self):
		self.nlp          = English()
		self.nlp.max_length = 2_000_000
		self.nlp.add_pipe('sentencizer')

	# Convert text to sentences
	#--------------------------------------------------
	def to_sentences(self, text):
		lines = [line.strip() for line in text.splitlines() if line.strip()]

		chunk_size = 200_000
		parts      = []
		for line in lines:
			parts.extend([line[i:i + chunk_size] for i in range(0, len(line), chunk_size)])

		sents = []
		for doc in self.nlp.pipe(parts, batch_size=32):
			for sent in doc.sents:
				st = sent.text.strip()
				if st:
					sents.append(st)

		return sents
