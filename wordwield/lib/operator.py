import os, json
from datetime import datetime

from .o import O


class Operator:
	def __init__(self, name=None):
		self.name = name
		self.ww   = type(self).ww

	async def __call__(self, *args, **kwargs):
		return await self.invoke(*args, **kwargs)

	async def invoke(self, *args, **kwargs):
		raise NotImplementedError('Operator must implement invoke method')

	def __repr__(self) -> str:
		return f'<Operator {type(self).__name__}>'

