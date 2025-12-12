# Retrieves an array of expertise factoids from project expertise files

from wordwield               import ww
from wordwield.lib           import O, Registry
from wordwield.operators     import Agent
from wordwield.services.expertise import Expertise


class Expert(Agent):

	#=================================================
	# Public methods
	#=================================================

	async def invoke(self, text, karma=0.5, ap_prev=None, show_chunks=False):
		texts, ap_next = Expertise().search(text, k=5, ap_prev=ap_prev, karma=karma)
		if show_chunks:
			n = 1
			print()
			for text in texts:
				print(f'{n}: {text}')
				n += 1
			print()
		return texts, ap_next
