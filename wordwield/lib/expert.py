from wordwield.lib import O, Agent


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
		agent = self.AgentType.load(name)
		print('Loaded', agent.to_dict())
		read_vars = await self.read(agent)
		print('Read', read_vars)
		self.to_vars(read_vars)
		print('Vars', self._vars)
		prompt = self.fill(self.template)
		print('Prompt', prompt)
		result = await self.ask(prompt=prompt, schema=self.ResponseType)
		await self.write(result)
