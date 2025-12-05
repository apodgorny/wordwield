# Retrieves an array of expertise factoids from project expertise files


from wordwield.lib       import O, Registry
from wordwield.operators import Agent


class Expert(Agent):

	# Public methods
	#########################################################################

	async def invoke(self):
		return ['foo', 'bar']