# ======================================================================
# RAG orchestration over semantic addresses (Vid-centric).
# ======================================================================

import torch as T
from collections import defaultdict

from wordwield.core.base.service import Service
from wordwield.core.db           import SemanticAtom
from wordwield.core.vdb          import Vdb
from wordwield.core.semantic     import Semantic
from wordwield.core.vid          import Vid


class RagService(Service):

	# To initialize vector database and hydrate it from persistent atoms.
	# ------------------------------------------------------------------
	def initialize(self):
		self.dim = Semantic('warmup').dim
		self.vdb = Vdb(self.dim)
		self._hydrate()

	# ==================================================================
	# PRIVATE METHODS
	# ==================================================================

	# To hydrate VDB from all non-temporary semantic atoms.
	# ------------------------------------------------------------------
	def _hydrate(self):
		atoms = SemanticAtom.get(Vid(temporary=False))

		print(f'Hydrating with {len(atoms)} atoms')

		if atoms:
			by_domain = defaultdict(list)

			for aid, data in atoms.items():
				v = Vid(id=aid)
				by_domain[v.domain].append((aid, data['vector']))

			for domain_id, items in by_domain.items():
				ids, vecs = zip(*items)
				self.vdb.add(domain_id, list(ids), T.stack(list(vecs)))

	# To persist semantic atoms and register them in VDB.
	# ------------------------------------------------------------------
	def _set_semantic(self, vid_base: Vid, semantic: Semantic, mtime: int, temporary: bool):
		ids     = []
		vectors = []

		for item, (text, vector) in enumerate(zip(semantic.texts, semantic.vectors)):
			vid = Vid(
				domain    = vid_base.domain,
				doc       = vid_base.doc,
				item      = item,
				temporary = temporary
			)

			SemanticAtom.set(
				vid    = vid,
				text   = text,
				vector = vector,
				mtime  = mtime
			)

			ids.append(vid.id)
			vectors.append(vector)

		self.vdb.add(vid_base.domain, ids, T.stack(vectors))
		self.ww.db.commit()

		return None

	# To remove semantic atoms by Vid mask.
	# ------------------------------------------------------------------
	def _unset(self, vid: Vid):
		atoms = SemanticAtom.get(vid)
		ids   = []

		if atoms:
			ids = list(atoms.keys())
			self.vdb.remove_ids(vid.domain, ids)

			for aid in ids:
				SemanticAtom.unset(aid)

			self.ww.db.commit()

		return ids

	# ==================================================================
	# PUBLIC METHODS
	# ==================================================================

	# To add or update semantic content under Vid.
	# ------------------------------------------------------------------
	def set(self, vid: Vid, text: str, mtime: int = 0, temporary: bool = False):
		existing = SemanticAtom.get(
			Vid(
				domain    = vid.domain,
				doc       = vid.doc,
				item      = None,
				temporary = None
			)
		)

		max_mtime = None
		for data in existing.values():
			if data['mtime'] is not None:
				max_mtime = data['mtime'] if max_mtime is None else max(max_mtime, data['mtime'])

		if existing and max_mtime is not None and mtime <= max_mtime:
			return False

		if existing:
			self._unset(Vid(domain=vid.domain, doc=vid.doc))

		semantic = Semantic(text)
		self._set_semantic(vid, semantic, mtime, temporary)

		return True

	# To remove semantic content by Vid mask.
	# ------------------------------------------------------------------
	def unset(self, vid: Vid):
		return self._unset(vid)

	# To search semantic space within a domain.
	# ------------------------------------------------------------------
	def search(self, query: str, vid: Vid, top_k: int = 10):
		result = {}
		qvec   = Semantic(query).vectors[0]

		seeds = self.vdb.query(
			vid.domain,
			qvec,
			top_k
		)

		by_doc = defaultdict(list)
		for sid in seeds:
			v = Vid(id=sid)
			by_doc[v.doc].append(sid)

		for doc_id, ids in by_doc.items():
			semantic = Semantic('', sentencize=False)
			semantic.load(ids)
			result[doc_id] = semantic.search(query)

		return result
