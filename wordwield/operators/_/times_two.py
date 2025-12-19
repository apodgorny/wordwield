from wordwield.core import Operator, O


class TimesTwo(Operator):
	'''Plugin operator that multiplies input by two.'''
	
	class InputType(O):
		x: int

	class OutputType(O):
		x: int
	
	async def invoke(self, x):
		return x * 2
