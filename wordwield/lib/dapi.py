import asyncio, os

from enum                 import Enum
from typing               import Any, Callable, Type, List, Dict

from fastapi              import APIRouter
from fastapi.responses    import JSONResponse
from sqlalchemy           import create_engine
from sqlalchemy.orm       import sessionmaker

from .string              import String
from .odb                 import ODB
from wordwield.lib.record import Base
from .dapi_exception      import DapiException

########################################################################

class Dapi:
	def __init__(self, *services):
		self.router      = APIRouter(prefix='/wordwield')
		self.db          = None
		self.app         = None
		self.project     = None
		self.odb         = ODB
		self.odb.session = None
		self.services    = services
		

		print('\nDAPI Controller is initiated\n')

	def start(self, app):
		self.app = app
		self.app.include_router(self.router)
		
	async def initialize_services(self):
		for cls in self.services:
			service      = cls(self)
			service_name = String.camel_to_snake(cls.__name__)
			if isinstance(service, DapiService) and hasattr(service, 'initialize'):
				setattr(self, service_name, service)
				await service.initialize()

	async def set_project(self, **kwargs):
		project_name   = kwargs['PROJECT_NAME']
		project_path   = kwargs['PROJECT_PATH']
		log_dir        = kwargs['LOG_DIR']
		expertise_dir  = kwargs['EXPERTISE_DIR']

		log_path       = os.path.join(project_path, log_dir)
		expertise_path = os.path.join(project_path, expertise_dir)
		db_name        = f'{String.camel_to_snake(project_name)}.db'
		db_path        = os.path.join(project_path, db_name)
		db_url         = f'sqlite:///{db_path}'

		if os.path.exists(db_path) and not os.access(db_path, os.W_OK):
			raise RuntimeError(f'❌ Cannot write to DB file: `{db_path}` — it is read-only.')

		engine   = create_engine(db_url, connect_args={'check_same_thread': False}, echo=False)
		Session  = sessionmaker(autocommit=False, autoflush=False, bind=engine)
		session  = Session()

		self.db  = session
		self.odb.session = self.db

		Base.metadata.create_all(bind=engine)

		self.project = {
			**kwargs,
			'LOG_PATH'       : log_path,
			'EXPERTISE_PATH' : expertise_path,
			'DB_PATH'        : db_path,
			'DB_URL'         : db_url
		}

		await self.initialize_services()



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

