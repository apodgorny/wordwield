from pydantic     import BaseModel
from typing       import Any
from lib.operator import Operator


class Recursor(Operator):
	'''Recursively calls an operator and builds a tree structure using its list output.''' 

	class InputType(BaseModel):
		generator_name  : str
		generator_input : dict
		depth           : int
		spread          : int
		breadcrumbs     : list[str] = None

	class OutputType(BaseModel):
		value : dict

	async def invoke(
		self,
		generator_name  : str,
		generator_input : dict,
		depth           : int       = 1,
		spread          : int       = 1,
		breadcrumbs     : list[str] = None
	):
		breadcrumbs = breadcrumbs or []
		breadcrumbs = breadcrumbs.copy()
		result = {
			'in'  : generator_input['item'],
			'out' : []
		}
		if depth > 0:
			print(breadcrumbs)
			generator_input = { **generator_input, 'spread': spread, 'breadcrumbs' : breadcrumbs }
			call_result     = await call(generator_name, generator_input)

			breadcrumbs.append(generator_input['item'])

			if depth > 1:
				for item in call_result:
					new_generator_input = {
						**generator_input,     # сохраняем все старые ключи
						'item'        : item,  # обновляем только item
						'breadcrumbs' : breadcrumbs
					}
					result_item = await recursor(
						generator_name  = generator_name,
						generator_input = new_generator_input,
						depth           = depth-1,
						spread          = spread,
						breadcrumbs     = breadcrumbs
					)
					result['out'].append({'in': item, 'out': result_item['out']})
			else:
				for item in call_result:
					result['out'].append({'in': item, 'out': []})
		return result