from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

from wordwield.core.base.reranker import Reranker


class LateInteractionReranker(Reranker):

	# Init
	# ----------------------------------------------------------------------
	def __init__(self):
		# Load ColBERTv2 model & tokenizer just once (at top level)
		self.tokenizer = AutoTokenizer.from_pretrained('colbert-ir/colbertv2.0')
		self.model     = AutoModel.from_pretrained('colbert-ir/colbertv2.0')
		self.model.eval()

	# Get token-level embeddings, ignore [CLS] and [SEP]
	# ----------------------------------------------------------------------
	def get_token_embeddings(self, text):
		inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=128)
		with torch.no_grad():
			outputs = self.model(**inputs)
		input_ids = inputs['input_ids'][0]
		keep_indices = (input_ids != self.tokenizer.cls_token_id) & (input_ids != self.tokenizer.sep_token_id)
		return outputs.last_hidden_state[0][keep_indices]  # (filtered_seq_len, hidden_dim)

	# query_emb: (m, d), doc_emb: (n, d)
	# ----------------------------------------------------------------------
	def get_colbert_score(self, query_emb, doc_emb):
		sim = F.cosine_similarity(query_emb.unsqueeze(1), doc_emb.unsqueeze(0), dim=2)  # (m, n)
		max_sim, _ = sim.max(dim=1)  # (m,)
		return max_sim.sum().item()

	# Precompute query embeddings once / Sort results by late_interaction_score descending
	# ----------------------------------------------------------------------
	def rerank(self, query, texts):
		query_emb = self.get_token_embeddings(query)
		scores = []
		for text in texts:
			text_emb = self.get_token_embeddings(text)
			scores.append(self.get_colbert_score(query_emb, text_emb))
		return scores
