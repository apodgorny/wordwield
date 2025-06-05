from __future__ import annotations

import os, ast, re
import uuid
import inspect

from typing          import Dict, List, Any

from pydantic        import BaseModel

from dapi.db         import OperatorRecord
from dapi.schemas    import OperatorSchema
from lib        import (
	String,
	DapiService,
	DapiException,
	DatumSchemaError,
	ExecutionContext,
	Operator,
	Module,
	Model,
	Python,
	is_reserved
)

OPERATOR_DIR = os.path.join(
	os.environ.get('PROJECT_PATH'),
	os.environ.get('OPERATOR_DIR', 'operators')
)


@DapiService.wrap_exceptions()
class OperatorService(DapiService):
	'''Service for managing operators.'''

	def __init__(self, dapi):
		self.dapi              = dapi
		self.i                 = ''
		self._operator_classes = {}  # name → operator class

	async def initialize(self):
		await super().initialize()
		await self._register_plugin_operators()

	############################################################################

	def _get_operator_globals(self, context):
		operator_globals = {
			'Operator'   : Operator,
			'BaseModel'  : BaseModel,
			'print'      : print,
			'len'        : len,
			'type'       : type,
			'isinstance' : isinstance,

			'list'       : list,
			'dict'       : dict,
			'str'        : str,
			'int'        : int,
			'float'      : float,
			'bool'       : bool,
			'set'        : set,
			'tuple'      : tuple,

			'Dict'       : Dict,
			'List'       : List,
			'Any'        : Any
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
			input,
			prompt,
			response_schema,

			model_id    = 'ollama::gemma3:4b',
			temperature = 0.0
		):
			return await Model.generate(
				prompt          = prompt,
				input           = input,
				response_schema = response_schema,
				model_id        = model_id,
				temperature     = temperature
			)

		operator_globals['ask'] = _ask
		#-----------------------------------------------------------------#
		return operator_globals

	def _generate_proxy_operator(self, code: str) -> str:
		tree       = ast.parse(code)
		cls        = next(n for n in tree.body if isinstance(n, ast.ClassDef))
		method     = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'invoke')
		args       = [a.arg for a in method.args.args if a.arg != 'self']
		arglist    = ', '.join(args)
		snake_name = String.to_snake_case(cls.name)

		return (
			f'class {cls.name}Proxy(Operator):\n'
			f'\tasync def invoke(self, {arglist}):\n'
			f'\t\treturn await {snake_name}({arglist})'
		)

	async def _register_plugin_operators(self):
		await self.delete_all()
		classes = Module.load_package_classes(Operator, OPERATOR_DIR)

		print(String.underlined('\nUnrestricted operators:'))
		for name, operator_class in classes.items():
			if not hasattr(operator_class, 'invoke'):
				continue

			if is_reserved(name):
				raise ValueError(f'Can not load operator `{name}` - the name is reserved')

			with open(os.path.join(OPERATOR_DIR, f'{name}.py')) as f:
				code = f.read()

			try:
				print(f'  - {name}')
				schema = OperatorSchema(
					name         = name,
					class_name   = operator_class.__name__,
					restrict     = False,
					input_type   = operator_class.InputType.model_json_schema(),
					output_type  = operator_class.OutputType.model_json_schema(),
					code         = code,
					description  = (operator_class.__doc__ or '').strip() or ''
				)

				await self.create(schema, replace=True)

			except DapiException as e:
				if e.detail.get('severity') == 'beware':
					continue
				raise
			except:
				print('Failed loading:', name)
				raise

		print()

	############################################################################

	def validate_name(self, name: str) -> None:
		if is_reserved(name):
			raise DapiException(
				status_code = 422,
				detail      = f'Can not create operator `{name}` - the name is reserved',
				severity    = DapiException.HALT
			)

	def require(self, name: str) -> OperatorRecord:
		operator = self.dapi.db.get(OperatorRecord, name)
		if not operator:
			raise DapiException(
				status_code = 404,
				detail      = f'Operator `{name}` does not exist',
				severity    = DapiException.HALT
			)
		operator.config = operator.config if operator.config else {}
		return operator

	############################################################################

	def exists(self, name) -> bool:
		return bool(self.dapi.db.get(OperatorRecord, name))

	async def create(self, schema: OperatorSchema, replace=False) -> bool:
		try:
			self.validate_name(schema.name)
			if self.exists(schema.name) and replace:
				await self.delete(schema.name)

			# schema.model_dump(exclude_unset=True))

			record = OperatorRecord(**schema.model_dump())
			self.dapi.db.add(record)
			self.dapi.db.commit()
			return schema.name
		except Exception as e:
			pass

	async def get(self, name: str) -> dict:
		record = self.require(name)
		return record.to_dict()

	async def get_all(self) -> list[dict]:
		return [op.to_dict() for op in self.dapi.db.query(OperatorRecord).all()]

	async def get_operator_sources(self) -> list[str]:
		"""Get a list of all operator names/sources."""
		operators = await self.get_all()
		return [op['name'] for op in operators]

	async def delete(self, name: str) -> None:
		record = self.require(name)
		self.dapi.db.delete(record)
		self.dapi.db.commit()

	async def delete_all(self) -> None:
		'''Delete all restricted operators.'''
		self.dapi.db.query(OperatorRecord)             \
			.filter(OperatorRecord.restrict.is_(True)) \
			.delete(synchronize_session=False)
		self.dapi.db.commit()

	async def get_input_dict(self, operator_name: str, args: list[Any], kwargs: dict[str, Any]) -> dict:
		'''
		Builds and validates the input dictionary for an operator call
		from positional args and keyword kwargs.
		'''
		operator        = await self.get(operator_name)
		input_schema    = operator['input_type']
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
						f'Operator `{operator_name}` declares only {len(expected_fields)} input field'
						f'{"s" if len(expected_fields) != 1 else ""}, but received {len(args)} positional argument'
						f'{"s" if len(args) != 1 else ""}.'
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
						f'Operator `{operator_name}` does not declare fields: {", ".join(unexpected_keys)} '
						f'in its InputType, but they were passed as input.'
					),
					error_type = 'UnexpectedKwargs',
					extra      = { 'unexpected': list(unexpected_keys) }
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
							f'in its InputType, but it was not provided.'
						),
						error_type = 'MissingRequired',
						extra      = { 'missing': param, 'provided': list(provided.keys()) }
					),
					severity = DapiException.HALT
				)

		return parameters

	async def get_output_dict(self, operator_name: str, output: Any) -> dict:
		'''
		Wraps a raw operator output (single value or tuple) into a validated dict
		according to the operator's OutputType schema.
		'''
		record          = await self.get(operator_name)
		expected_fields = list(record['output_type'].get('properties', {}).keys())

		# Utility to build detailed error context, phrased from operator's perspective
		def make_detail(message: str, error_type: str, extra: dict = {}) -> dict:
			return {
				'message'    : message,
				'error_type' : error_type,
				'operator'   : operator_name,
				'expected'   : expected_fields,
				'actual'     : output,
				**extra
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
						f'{", ".join(expected_fields)} — got {type(output).__name__} instead.'
					),
					error_type = 'InvalidOutputType',
					extra      = { 'actual_type': type(output).__name__ }
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

	async def unwrap_output(self, operator_name: str, output_dict: dict) -> Any: # TODO: refactor
		'''
		Transforms an output dict into a value or tuple for use inside user code.
		'''
		expected_fields = list(output_dict.keys())

		if not expected_fields:
			return None

		if len(expected_fields) == 1:
			return output_dict[expected_fields[0]]

		return tuple(output_dict[field] for field in expected_fields)

	async def call_external_operator(self, name: str, args: list, kwargs: dict, context: ExecutionContext) -> Any:
		'''
		Handles external operator call by packing input from local variables,
		invoking the operator, and unpacking the output for use.
		'''
		input_dict  = await self.get_input_dict(name, args, kwargs)  # Step 1: Pack input
		output_dict = await self.invoke(name, input_dict, context)   # Step 2: Full invocation
		result      = await self.unwrap_output(name, output_dict)    # Step 3: Unpack output to tuple

		return result

	async def invoke(self, name: str, input: dict, context: ExecutionContext) -> dict:
		if context is None:
			raise ValueError('ExecutionContext must be explicitly provided')
		
		self.i = context.i

		operator         = self.require(name)
		operator_globals = self._get_operator_globals(context)
		output           = ''

		try:
			context.push(
				name        = name,
				lineno      = 1,
				restrict    = operator.restrict,
				importance  = 1,
				detail      = str(input)
			)
			instance = Python(
				operator_name          = name,
				operator_class_name    = operator.class_name,
				input_dict             = input,
				code                   = operator.code,
				execution_context      = context,
				operator_globals       = operator_globals,
				call_external_operator = self.call_external_operator,
				restrict               = operator.restrict
			)

			result = await instance.invoke()
			output = await self.get_output_dict(name, result)
			return output

		except Exception as e:
			raise DapiException.consume(e)

		finally:
			context.pop(detail=str(output))
