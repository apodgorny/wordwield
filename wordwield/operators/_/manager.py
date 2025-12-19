from wordwield import ww


class Manager(ww.operators.Agent):
	async def write(self):
		self.streams_by_role.invoke_stream.write(
			self.state.next_agent_name
		).save()
	