from wordwield import ww


class Tester(ww.operators.Agent):
	
	async def write(self):
		if self.state.approve:
			self.project.streams_by_role.prod_stream.write(
				self.project.guessed_number
			).save()
		else:
			self.project.streams_by_role.bug_stream.write(
				self.state.directions
			).save()
	