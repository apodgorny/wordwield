# ======================================================================
# Base class for deterministic execution tools.
# ======================================================================

from wordwield.core.base     import Operator
from wordwield.core.registry import Registry


class Tool(Operator):

	# Initialize tool instance
	# ----------------------------------------------------------------------
	def __init__(self, name=None):
		super().__init__(name=name)                      # Initialize operator base
		Registry('state', self)                          # Register state registry


	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Execute deterministic tool logic
	# ----------------------------------------------------------------------
	async def invoke(self, *args, **kwargs):
		raise NotImplementedError(
			f'Tool `{self.__class__.__name__}` must implement invoke method'
		)
