import asyncio, traceback

from enum                 import Enum
from typing               import Any, Callable, Type, List, Dict

from fastapi              import APIRouter
from fastapi.responses    import JSONResponse

from .string              import String
from .odb                 import ODB
from wordwield.db         import Base, engine, session
from .dapi_exception      import DapiException

########################################################################

class Dapi:
	def __init__(self, *services):
		self.router      = APIRouter(prefix='/wordwield')
		self.db          = session
		self.app         = None
		self.odb         = ODB
		self.odb.session = self.db

		for cls in services:
			setattr(self, String.camel_to_snake(cls.__name__), cls(self))

		Base.metadata.create_all(bind=engine)

		print('\nDAPI Controller is initiated\n')

	def start(self, app):
		self.app = app
		self.app.include_router(self.router)
		
	async def initialize_services(self):
		"""Initialize all services asynchronously."""
		for service_name in dir(self):
			service = getattr(self, service_name)
			if isinstance(service, DapiService) and hasattr(service, 'initialize'):
				await service.initialize()

########################################################################		

class DapiService:
	'''Base service with exception-wrapping decorator.'''

	def __init__(self, dapi):
		self.dapi = dapi

	async def initialize(self):
		pass

	@classmethod
	def wrap_exceptions(cls):
		'''Class decorator that wraps all public methods with exception handling.'''

		def handle_exception(e):
			raise DapiException.consume(e)

		def create_wrapper(method):
			if asyncio.iscoroutinefunction(method):
				async def wrapper(*args, **kwargs):
					try:
						return await method(*args, **kwargs)
					except Exception as e:
						raise
						# return handle_exception(e)
			else:
				def wrapper(*args, **kwargs):
					try:
						return method(*args, **kwargs)
					except Exception as e:
						raise
						# return handle_exception(e)

			return wrapper

		def decorate(target_cls):
			for attr_name in dir(target_cls):
				if attr_name.startswith('_'):
					continue
				method = getattr(target_cls, attr_name)
				if callable(method):
					setattr(target_cls, attr_name, create_wrapper(method))
			return target_cls

		return decorate

