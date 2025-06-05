import os, json
from datetime import datetime
from typing import Callable

from .o                 import O
from .string            import String
from .autoargs          import autodecorate
from .execution_context import ExecutionContext


LOG_PATH = os.path.join(
	os.environ.get('PROJECT_PATH'),
	os.environ.get('LOG_DIR')
)


class Operator:
	'''Base interface for any executable operator: static, dynamic, composite.'''

	@property
	def input_type(self):
		return self.__class__.InputType

	@property
	def output_type(self):
		return self.__class__.OutputType

	@classmethod
	def input_fields(cls) -> list[str]:
		return list(cls.InputType.model_fields.keys())

	@classmethod
	def output_fields(cls) -> list[str]:
		return list(cls.OutputType.model_fields.keys())

	def __init__(self, name, globals):
		self.name    = name
		self.globals = globals

		if not (
			hasattr(self.__class__, 'InputType')             and
			isinstance(self.__class__.InputType, type)       and
			issubclass(self.__class__.InputType, O)
		):
			raise TypeError(f'InputType of operator `{self.__class__.__name__}` must be a class subclassing O')

		if not (
			hasattr(self.__class__, 'OutputType')            and
			isinstance(self.__class__.OutputType, type)      and
			issubclass(self.__class__.OutputType, O)
		):
			raise TypeError(f'OutputType of operator `{self.__class__.__name__}` must be a class subclassing O')

	def log(self, *args, name=None, clear=False, timestamp=False):
		file_name = f'{self.name}.{name}.log' if name else f'{self.name}.log'
		filepath  = os.path.join(LOG_PATH, file_name)
		mode      = 'w' if clear else 'a'
		value     = '\n'.join([arg.strip() if isinstance(arg, str) else json.dumps(arg, ensure_ascii=False, indent=4)for arg in args])

		if timestamp:
			timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			log_line  = f'[{timestamp}]\n{value}\n'
		else:
			log_line  = f'{value}\n'

		with open(filepath, mode, encoding='utf-8') as f:
			f.write(log_line)

	async def call(self, name, **kwargs):
		return await self.globals['call'](name, *[], **kwargs)

	async def invoke(self):
		'''Execute operator and return output.'''
		raise NotImplementedError('Operator must implement invoke method')

	def __repr__(self) -> str:
		return f'<Operator {self.__class__.__name__}>'
