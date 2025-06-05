import os, re

from pydantic import BaseModel

from .module          import Module
from .string          import String
from .o               import O
from .dapi_exception  import DapiException
from .transform       import T

PROJECT_PATH = os.environ.get('PROJECT_PATH')
MODELS_DIR   = os.environ.get('MODELS_DIR')
MODELS_PATH  = os.path.join(PROJECT_PATH, MODELS_DIR)


class Model:

	def __init__(self, name: str):
		self.name = name

	##################################################################

	@classmethod
	def load(cls, model_id: str) -> 'Model':
		if '::' not in model_id:
			raise ValueError(f'Invalid model_id: `{model_id}`. Expected format `provider::name`')

		provider, name = model_id.split('::', 1)
		file_path      = os.path.join(MODELS_PATH, f'model_{provider}.py')

		try:
			model_cls         = Module.find_class_by_base(cls, file_path)
			instance          = model_cls(name)
			instance.model_id = model_id
			return instance

		except FileNotFoundError:
			raise ValueError(f'Model file not found: `{file_path}`')

		except AttributeError:
			raise ValueError(f'No subclass of Model found in `{file_path}`')

	@classmethod
	async def generate(
		cls,
		
		prompt         : str,
		response_model : O,

		model_id       : str        = 'ollama::gemma3:4b',
		role           : str        = 'user',
		temperature    : float      = 0.0,
		system         : str | None = None

	) -> dict:
		try:
			if not issubclass(response_model, O):
				raise ValueError(f'Model.generate requires `response_model` to be a subclass of `O`, but received `{type(response_model)}`')

			model  = Model.load(model_id)
			result = await model(
				prompt          = prompt,
				response_schema = response_model.to_schema(),
				role            = role,
				temperature     = temperature,
				system          = system
			)

			# Validate output
			response_model(**result)

			# Unpack to tuple of attributes or single value to match operator output convention
			result = T(T.DATA, T.ARGUMENTS, result)
			return result

		except Exception as e:
			raise DapiException.consume(e)
