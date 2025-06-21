import os, json
from datetime import datetime

from .o import O


class Operator:
	ww = None

	def __init__(self, name=None, schema:O=None):
		self.name   = name
		self.schema = schema
		if schema is not None and name is not None:
			if O.is_o_type(schema):
				self.schema = schema.load(name)
			elif not O.is_o_instance(schema):
				raise TypeError(f'Invalid schema type: expected O class or instance, got {type(schema)}')

	async def __call__(self, *args, **kwargs):
		await self.init()
		return await self.invoke(*args, **kwargs)
	
	async def init(self):
		pass

	async def invoke(self, *args, **kwargs):
		raise NotImplementedError('Operator must implement invoke method')

	def __repr__(self) -> str:
		return f'<Operator {self.__class__.__name__}>'

