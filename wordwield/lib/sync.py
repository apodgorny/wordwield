from .operator import Operator
from .o        import O


class Sync(Operator):
	class InputType(O):
		operators : list[str]
		items     : list[dict]

	class OutputType(O):
		items : list[dict]

	async def invoke(self, operators, items):
		items_out = []
		for operator in operators:
			items_out += await self.call(operator, items)
		return items_out