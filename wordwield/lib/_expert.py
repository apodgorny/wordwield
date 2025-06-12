from .agent import Agent
from .o     import O

from schemas.schemas import (
	AgentSchema
)


class Expert(Agent):
	class InputType(O):
		name: str

	class OutputType(O):
		text: str

	async def read(self, agent) -> dict:
		for var in agent.read:
			print(var.name)

	async def write(self, result: O):
		pass

	async def invoke(self, name):
		agent = AgentSchema.load(name)
		read_vars = await self.read(agent)
		self.to_vars(read_vars)
		prompt = self.fill(self.template)
		result = await self.ask(prompt=prompt)
		await self.write(result)
