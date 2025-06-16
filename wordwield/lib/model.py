import os, re

from pydantic import BaseModel

from .module          import Module
from .string          import String
from .o               import O
from .t               import T
from .ww_exception  import WwException


class Model:

	##################################################################

	@classmethod
	def load(cls, model_id, models_registry):
		if '::' not in model_id:
			raise ValueError(f'Invalid model_id: `{model_id}`. Expected format `provider::name`')

		provider, model_name = model_id.split('::', 1)
		model_key            = f'{String.snake_to_camel(provider)}Model'
		model_class          = models_registry[model_key]
		model                = model_class(model_name)
		model.model_id       = model_id

		return model
		
	##################################################################
		
	@classmethod
	async def generate(
		cls,
		ww,
		
		prompt          : str,
		response_schema : O,

		model_id        : str        = 'ollama::gemma3:4b',
		role            : str        = 'user',
		temperature     : float      = 0.0,
		system          : str | None = None

	) -> dict:
		try:
			if not issubclass(response_schema, O):
				raise ValueError(f'Model.generate requires `response_model` to be a subclass of `O`, but received `{type(response_schema)}`')

			model  = Model.load(model_id, ww.models)
			result = await model(
				prompt          = prompt,
				response_schema = response_schema.to_schema(),
				role            = role,
				temperature     = temperature,
				system          = system
			)

			# Validate output
			response_schema(**result)
			return result

		except Exception as e:
			raise WwException.consume(e)
