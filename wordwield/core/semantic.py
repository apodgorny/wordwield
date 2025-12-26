from wordwield                   import ww
from wordwield.core.sentencizers import PysbdSentencizer as Sentencizer

class Semantic:
	def __init__(self, text, sentencize=True):
		self.encoder     = ww.encoder
		self.sentencizer = Sentencizer()
		self.dim         = self.encoder.model.config.hidden_size

		if sentencize:
			self.texts   = self.sentencizer.to_sentences(text)
			self.vectors = self.encoder.encode_sequence(self.texts)
		else:
			self.texts   = [text]
			self.vectors = [self.encoder.encode(text)]