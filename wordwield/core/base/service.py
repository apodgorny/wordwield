# ======================================================================
# Shared singleton base for services.
# ======================================================================

class Service:
	ww           = None   # Set at instantiation
	_instance    = None
	# _initialized = False

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		if '__init__' in cls.__dict__ and cls.__dict__['__init__'] is not Service.__init__:
			raise TypeError('Services must not override __init__; implement `initialize` instead.')

	# Provide singleton instance creation
	# ----------------------------------------------------------------------
	def __new__(cls, *args, **kwargs):
		result = cls._instance
		if result is None:
			result = super().__new__(cls)
			cls._instance = result
		return result

	# # Generic initializer that runs once per singleton instance
	# # ----------------------------------------------------------------------
	# def __init__(self, *args, **kwargs):
	# 	if not self._initialized:
	# 		self.initialize(*args, **kwargs)
	# 		self._initialized = True

	# Must be implemented by subclasses
	# ----------------------------------------------------------------------
	def initialize(self, *args, **kwargs):
		raise NotImplementedError('`initialize` must be implemented on Service subclasses.')
	
	# Logging
	# ----------------------------------------------------------------------
	def log(self, *args):
		if self.ww.verbose:
			self.ww.log_info(*args)
