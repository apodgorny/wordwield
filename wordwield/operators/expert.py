from wordwield.lib import O, T
from wordwield.operators.agent import Agent

from wordwield.schemas.project import (
	ExpertSchema
)


class Expert(Agent):
	class InputType(O):
		name: str

	class OutputType(O):
		status: int

	async def read(self) -> dict:
		values = {}
		for var in self.data.read:
			values[var.varname] = await stream_read(var.streams, var.length)
		return values

	async def write(self):
		# print('IN WRITE', self.vars)
		write = None
		if self.data.mode == 'binary':
			is_true = self.vars['is_true']
			write   = self.data.write_true if is_true else self.data.write_false
		else:
			write   = self.data.write

		for var in write:
			value = self.vars.get(var.varname, None)
			if value is None:
				raise KeyError(f'Could not write to stream. Variable `{var.varname}` is not found in agent `{self.name}`')
			if isinstance(value, list):
				if len(value) == 0:
					raise ValueError(f'Could not write to stream. Variable `{var.varname}` is empty in agent `{self.name}`')
				value = value[0]
			await stream_write(var.streams, value)

	async def invoke(self, name):
		self.data = ExpertSchema.load(name)
		read_vars = await self.read()
		self.to_vars(read_vars)
		schema = await self.schema(self.data.response_type)
		prompt = self.fill(self.data.template)
		result = await self.ask(prompt=prompt, schema=schema)
		packed = schema.pack(result)
		self.to_vars(packed.to_dict())
		await self.write()
		return 0
