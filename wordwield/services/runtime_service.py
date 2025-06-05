from __future__ import annotations
import random, json, aiofiles

from typing   import Any, Dict, List, Optional
from pydantic import BaseModel

from wordwield.lib import (
	DapiException,
	DapiService,
	ExecutionContext,
	Python,
	Model,
	String,

	O,
	Operator,
	Agent,
	Expert
)
from wordwield.schemas import OperatorSchema


@DapiService.wrap_exceptions()
class RuntimeService(DapiService):
	'''Handles execution of operators: input/output packing, invocation, context tracing.'''

	############################################################################

	def get_globals(self, context=None, type_classes=None):
		operator_globals = {
			'Operator'     : Operator,
			'Agent'        : Agent,
			'Expert'       : Expert,
 
			'O'            : O,
			'String'       : String,

			'BaseModel'    : BaseModel,
			'random'       : random,
			'json'         : json,
			'aiofiles'     : aiofiles,
		}

		#-----------------------------------------------------------------#
		async def _call(name, *args, **kwargs):
			if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
				kwargs = args[0]
				args   = []

			return await self.call_external_operator(
				name     = name,
				args     = list(args),
				kwargs   = kwargs,
				context  = context
			)

		operator_globals['call'] = _call
		#-----------------------------------------------------------------#
		async def _ask(
			prompt,
			response_model,

			model_id    = 'ollama::gemma3:4b',
			temperature = 0.0
		):
			return await Model.generate(
				prompt          = prompt,
				response_model  = response_model,
				model_id        = model_id,
				temperature     = temperature
			)

		operator_globals['ask'] = _ask
		#-----------------------------------------------------------------#

		if type_classes:
			operator_globals.update(type_classes)

		return operator_globals

	############################################################################

	async def get_registered_operator_names(self) -> set[str]:
		'''Returns a set of all registered operator names.'''
		operators = await self.dapi.definition_service.get_all()
		return {op['name'] for op in operators}

	async def call_external_operator(self, name: str, args: list, kwargs: dict, context: ExecutionContext) -> Any:
		'''External operator call from interpreted code.'''
		input_dict  = await self.get_input_dict(name, args, kwargs)  # Step 1: Pack input
		output_dict = await self.invoke(name, input_dict, context)   # Step 2: Full invocation
		result      = await self.unwrap_output(name, output_dict)    # Step 3: Unpack output to tuple
		return result

	async def invoke(self, name: str, input: dict, context: ExecutionContext) -> dict:
		if context is None:
			raise ValueError('ExecutionContext must be explicitly provided')

		self.i = context.i

		registered_operators = await self.get_registered_operator_names()
		type_classes         = await self.dapi.type_service.get_all(context)
		operator_globals     = self.get_globals(context, type_classes)
		operator             = self.dapi.definition_service.require(name)
		output               = ''

		try:
			context.push(
				name        = name,
				lineno      = 1,
				restrict    = operator.restrict,
				importance  = 1,
				detail      = str(input)
			)
			instance = Python(
				execution_context      = context,
				registered_operators   = registered_operators,
				extra_globals          = operator_globals,
				call_external_operator = self.call_external_operator,
				restrict               = operator.restrict
			)

			result = await instance.invoke(
				operator_name          = name,
				operator_class_name    = operator.class_name,
				input_dict             = input,
				code                   = operator.code
			)
			output = await self.get_output_dict(name, result)
			return output

		except Exception as e:
			raise DapiException.consume(e)

		finally:
			context.pop(detail=str(output))

	############################################################################

	async def get_input_dict(self, operator_name: str, args: list[Any], kwargs: dict[str, Any]) -> dict:
		'''
		Builds and validates the input dictionary for an operator call
		from positional args and keyword kwargs.
		'''
		operator        = self.dapi.definition_service.require(operator_name)
		input_schema    = operator.input_type
		expected_fields = list(input_schema.get('properties', {}).keys())
		required_fields = input_schema.get('required', [])

		# Utility to build detailed error context, phrased from operator's perspective
		def make_detail(message: str, error_type: str, extra: dict = {}) -> dict:
			return {
				'message'    : message,
				'error_type' : error_type,
				'operator'   : operator_name,
				'args'       : args,
				'kwargs'     : kwargs,
				'declared_input_fields': expected_fields,
				**extra
			}

		provided = {}

		# 1. Map positional args to declared fields in InputType
		for param, value in zip(expected_fields, args):
			provided[param] = value

		# 2. Fill remaining fields from keyword args
		for param in expected_fields:
			if param not in provided and param in kwargs:
				provided[param] = kwargs[param]

		# 3. Auto-inject self if present in schema
		if 'self' in expected_fields and 'self' not in provided:
			provided['self'] = None

		# 4. Fail if operator was defined with too few input fields
		if len(args) > len(expected_fields):
			raise DapiException(
				status_code = 422,
				detail      = make_detail(
					message    = (
						f'Operator `{operator_name}` declares only {len(expected_fields)} input field(s), '
						f'but received {len(args)} positional argument(s): {args}'
					),
					error_type = 'TooManyArgs'
				),
				severity = DapiException.HALT
			)

		# 5. Fail if keyword arguments are passed that are not defined in operator's InputType
		unexpected_keys = set(kwargs.keys()) - set(expected_fields)
		if unexpected_keys:
			raise DapiException(
				status_code = 422,
				detail      = make_detail(
					message    = (
						f'Operator `{operator_name}` received undeclared input fields: {", ".join(unexpected_keys)} '
					),
					error_type = 'UnexpectedKwargs'
				),
				severity = DapiException.HALT
			)

		# 6. Validate that all required parameters are present
		parameters = {}
		for param in expected_fields:
			if param in provided:
				parameters[param] = provided[param]
			elif param in required_fields:
				raise DapiException(
					status_code = 422,
					detail      = make_detail(
						message    = (
							f'Operator `{operator_name}` requires parameter `{param}` '
							f'in its InputType, but received {list(provided.keys())}'
						),
						error_type = 'MissingRequired'
					),
					severity = DapiException.HALT
				)

		return parameters

	############################################################################

	async def get_output_dict(self, operator_name: str, output: Any) -> dict:
		'''
		Wraps a raw operator output (single value or tuple) into a validated dict
		according to the operator's OutputType schema.
		'''
		operator        = self.dapi.definition_service.require(operator_name)
		expected_fields = list(operator.output_type.get('properties', {}).keys())

		# Utility to build detailed error context, phrased from operator's perspective
		def make_detail(message: str, error_type: str) -> dict:
			return {
				'message'    : message,
				'error_type' : error_type,
				'operator'   : operator_name,
				'expected'   : expected_fields,
				'actual'     : output
			}

		# 1. Fail if operator does not define any output fields at all
		if not expected_fields:
			raise DapiException(
				status_code = 500,
				detail      = make_detail(
					message    = f'Operator `{operator_name}` has no output fields defined in OutputType.',
					error_type = 'MissingOutputFields'
				),
				severity = DapiException.HALT
			)

		# 2. Single-field output — value must be scalar (not tuple/dict)
		if len(expected_fields) == 1:
			return { expected_fields[0]: output }

		# 3. Multi-field output — value must be tuple of correct length
		if not isinstance(output, tuple):
			raise DapiException(
				status_code = 422,
				detail      = make_detail(
					message    = (
						f'Operator `{operator_name}` must return a tuple with values for fields: '
						f'{", ".join(expected_fields)} — got {type(output).__name__} ({type(output).__name__}) instead.'
					),
					error_type = 'InvalidOutputType'
				),
				severity = DapiException.HALT
			)

		# 4. Tuple length mismatch — output must match exactly
		if len(output) != len(expected_fields):
			raise DapiException(
				status_code = 422,
				detail      = make_detail(
					message    = (
						f'Operator `{operator_name}` returned tuple of length {len(output)}, '
						f'but OutputType declares {len(expected_fields)} fields: {", ".join(expected_fields)}.'
					),
					error_type = 'OutputLengthMismatch'
				),
				severity = DapiException.HALT
			)

		# 5. Build named output dict from tuple
		return { field: value for field, value in zip(expected_fields, output) }

	############################################################################

	async def unwrap_output(self, operator_name: str, output_dict: dict) -> Any: # TODO: refactor
		'''
		Transforms an output dict into a value or tuple for use inside user code.
		'''
		expected_fields = list(output_dict.keys())

		if not expected_fields       : return None
		if len(expected_fields) == 1 : return output_dict[expected_fields[0]]

		return tuple(output_dict[field] for field in expected_fields)
