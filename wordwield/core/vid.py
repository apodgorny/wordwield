# ======================================================================
# Canonical semantic id (Vid): 4 × 16-bit layout
# [ domain | doc | item | flags ]
# ======================================================================

from wordwield.core.db.domain   import Domain
from wordwield.core.db.document import Document

_MASK = 0xFFFF

_SHIFT_FLAGS  = 0
_SHIFT_ITEM   = 16
_SHIFT_DOC    = 32
_SHIFT_DOMAIN = 48


class Vid:

	# Constructor
	# ----------------------------------------------------------------------
	def __init__(
		self,
		id        : int  | None = None,
		*,
		domain    : int  | None = None,
		doc       : int  | None = None,
		item      : int  | None = None,
		temporary : bool | None = None
	):
		if id is None:
			domain_id, doc_id = self._resolve(domain, doc)
			flags = Vid._encode_flag(temporary)
			self.id = (
				((domain or 0) & _MASK) << _SHIFT_DOMAIN |
				((doc    or 0) & _MASK) << _SHIFT_DOC    |
				((item   or 0) & _MASK) << _SHIFT_ITEM   |
				(flags         & _MASK)
			)
		else:
			self.id = int(id)

	# ----------------------------------------------------------------------
	def __int__(self):
		return self.id
	# ----------------------------------------------------------------------
	def __hash__(self):
		return self.id
	# ----------------------------------------------------------------------
	def __eq__(self, other):
		if isinstance(other, Vid):
			return self.id == other.id
		if isinstance(other, int):
			return self.id == other
		return False
	# ----------------------------------------------------------------------
	def __repr__(self):
		return (
			f'Vid(domain={self.domain}, doc={self.doc}, '
			f'item={self.item}, temp={self.temporary})'
		)

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Resolve string key and domain name to ids
	# ----------------------------------------------------------------------
	@staticmethod
	def _resolve(domain, doc):
		domain_id, doc_id = None, None

		if domain is not None:
			d = Domain.get(domain) if isinstance(domain, str) else domain
			if d is None: raise KeyError(f'Domain not found: `{domain}`')
			domain_id = d.id

		if doc is not None:
			r = Document.get(doc) if isinstance(doc, str) else doc
			if r is None: raise KeyError(f'Document not found: `{doc}`')
			doc_id = r.id

		return domain_id, doc_id

	# Encode tri-state flag into 2 bits, False (00), True (10), None (01,11)
	# ----------------------------------------------------------------------
	@staticmethod
	def _encode_flag(value: bool | None) -> int:
		if value is None: return 0b01  # None
		if value is True: return 0b10  # True
		return 0b00                    # False

	# Decode tri-state flag from 2 bits.
	# ----------------------------------------------------------------------
	@staticmethod
	def _decode_flag(bits: int) -> bool | None:
		none_bit = (bits >> 1) & 1
		bool_bit = bits & 1
		if none_bit: return None
		return bool(bool_bit)

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Properties
	# ----------------------------------------------------------------------
	@property
	def domain(self) -> int | None:	return (self.id >> _SHIFT_DOMAIN) & _MASK or None
	@property
	def doc(self)    -> int | None: return (self.id >> _SHIFT_DOC) & _MASK or None
	@property
	def item(self)   -> int | None: return (self.id >> _SHIFT_ITEM) & _MASK or None
	@property
	def flags(self)  -> int: return self.id & _MASK
	@property
	def temporary(self) -> bool | None: return Vid._decode_flag(self.flags & 0b11)
	
	# True if Vid points to a single concrete atom.
	# ----------------------------------------------------------------------
	@property
	def is_address(self) -> bool:
		return (
			self.domain    is not None and
			self.doc       is not None and
			self.item      is not None and
			self.temporary is not None
		)

	# SQLAlchemy condition builder
	# ----------------------------------------------------------------------
	def conditions(self, column):
		'''
		Build SQLAlchemy filter conditions for a column storing Vid int.
		column : sqlalchemy Column (e.g. SemanticAtom.id)
		Returns: list of SQLAlchemy binary expressions
		'''
		conds = []

		if self.domain is not None:
			conds += [(column.op('>>')(_SHIFT_DOMAIN)) == self.domain]              # domain match
		if self.doc is not None:
			conds += [(column.op('>>')(_SHIFT_DOC).op('&')(_MASK)) == self.doc]     # document match
		if self.item is not None:
			conds += [(column.op('>>')(_SHIFT_ITEM).op('&')(_MASK)) == self.item]   # item index match

		temp = self.temporary                                                       # tri-state flag

		if temp is None:
			conds += [(column.op('>>')(1).op('&')(1)) == 1]                         # temporary is None
		elif temp is True:
			conds += [(column.op('>>')(1).op('&')(1)) == 0]                         # not None
			conds += [(column.op('&')(1)) == 1]                                     # value = True
		else:
			conds += [(column.op('>>')(1).op('&')(1)) == 0]                         # not None
			conds += [(column.op('&')(1)) == 0]                                     # value = False

		return conds
