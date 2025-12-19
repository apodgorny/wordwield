import os, json
from datetime import datetime


class Operator:
	ww = None

	def __init__(self, name=None):
		self.name = name

	async def __call__(self, *args, **kwargs):
		await self.init()
		return await self.invoke(*args, **kwargs)
	
	async def init(self):
		pass

	async def invoke(self, *args, **kwargs):
		raise NotImplementedError('Operator must implement invoke method')

	def __repr__(self) -> str:
		return f'<Operator {self.__class__.__name__}>'
