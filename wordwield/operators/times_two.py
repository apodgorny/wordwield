from pydantic     import BaseModel
from lib.operator import Operator


class TimesTwo(Operator):
	'''Plugin operator that multiplies input by two.'''
	
	class InputType(BaseModel):
		x: int

	class OutputType(BaseModel):
		x: int
	
	async def invoke(self, x):
		return x * 2
