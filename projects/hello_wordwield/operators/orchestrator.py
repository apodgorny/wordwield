from wordwield import ww


class Orchestrator(ww.operators.Agent):
	agents = {
		'expert' : ww.operators.Expert
	}

	async def invoke(self, task):
		experise = await self.agents.expert('roi')
		for exp in experise:
			print(exp, end='\n\n')
