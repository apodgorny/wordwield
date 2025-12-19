from wordwield import ww


class Developer(ww.operators.Agent):

	async def write(self):
		self.project.streams_by_role.dev_stream.write(
			self.state.result
		).save()
	