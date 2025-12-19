import torch
import os

from sentence_transformers import SentenceTransformer, util

from wordwield.core.device import device
from wordwield.core.norm   import Norm
from wordwield.core.kaggle import Kaggle


#==================================================
# AP Decoder — manual workflow
#==================================================


class WordDecoder:
	def __init__(self, model_name=None, device_override=None):
		default     = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
		self.device = device_override or device
		self.model  = SentenceTransformer(model_name or default, device=self.device)

		self.words           = []
		self.word_embeddings = None

	#==================================================
	# PRIVATE METHODS
	#==================================================

	# Encode a list of words
	# ----------------------------------------------------------------------
	def _encode_words(self, words):
		return self.model.encode(
			words,
			convert_to_tensor    = True,
			normalize_embeddings = True
		)

	#==================================================
	# PUBLIC METHODS
	#==================================================

	# Load vocabulary
	# ----------------------------------------------------------------------
	def load(self):
		kaggle_dataset_id   = 'alexanderpodgorny/word-decoder'
		kaggle_dataset_file = 'word_decoder.pt'
		
		self.words           = []
		self.word_embeddings = None
		success              = False
		state                = Kaggle().load(kaggle_dataset_id, kaggle_dataset_file)

		if state:
			self.words           = state['words']
			self.word_embeddings = state['embeddings'].to(device)
			success              = True
			
		return success

	# Embed vocabulary into MiniLM space
	# ----------------------------------------------------------------------
	def embed(self, words):
		self.words           = list(words)
		self.word_embeddings = self._encode_words(self.words)
		return None

	# Decode AP vector into nearest words
	# ----------------------------------------------------------------------
	def decode(self, vector, top_k=20):
		# Your normalization. ONLY your Norm.
		vector = Norm.to_hypercube(vector).to(device)

		scores = util.cos_sim(vector, self.word_embeddings)[0]
		top    = torch.topk(scores, top_k)

		result = []
		for i in top.indices:
			result.append((self.words[i], float(scores[i])))

		return result

	# Save vocabulary + embeddings
	# ----------------------------------------------------------------------
	def save(self, path):
		torch.save(
			{
				'words'      : self.words,
				'embeddings' : self.word_embeddings.cpu()
			},
			path
		)
		return path
