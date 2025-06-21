from wordwield.lib import O


class ManagerResponseSchema(O):
	next_agent_name: str = O.Field(description='Agent name to be called next')

class DeveloperResponseSchema(O):
	result: str = O.Field(description='Your result')

class TesterResponseSchema(O):
	approve    : bool = O.Field(description='True if correct, false otherwise')
	directions : str  = O.Field(description='Directions to improve the result')