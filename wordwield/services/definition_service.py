from __future__ import annotations

import os
from typing import Any

from wordwield.lib  import DapiException, DapiService, is_reserved, Module, String, Operator

from wordwield.db      import OperatorRecord
from wordwield.schemas import OperatorSchema


OPERATOR_DIR = os.path.join(
	os.environ.get('PROJECT_PATH'),
	os.environ.get('OPERATOR_DIR', 'operators')
)


@DapiService.wrap_exceptions()
class DefinitionService(DapiService):
	'''Stores and manages operator definitions, including plugin loading and schema validation.'''

	async def initialize(self):
		await super().initialize()
		await self.register_plugin_operators()

	############################################################################

	def validate_name(self, name: str) -> None:
		if is_reserved(name):
			raise DapiException(
				status_code = 422,
				detail      = f'Can not create operator `{name}` - the name is reserved',
				severity    = DapiException.HALT
			)

	def require(self, name: str) -> OperatorRecord:
		op = self.dapi.db.get(OperatorRecord, name)
		if not op:
			raise DapiException(
				status_code = 404,
				detail      = f'Operator `{name}` does not exist',
				severity    = DapiException.HALT
			)
		op.config = op.config or {}
		return op

	############################################################################

	def exists(self, name: str) -> bool:
		return bool(self.dapi.db.get(OperatorRecord, name))

	async def create(self, schema: OperatorSchema, replace=False) -> bool:
		self.validate_name(schema.name)

		if self.exists(schema.name) and replace:
			await self.delete(schema.name)

		record = OperatorRecord(**schema.model_dump())
		self.dapi.db.add(record)
		self.dapi.db.commit()
		return schema.name

	async def get(self, name: str) -> dict:
		return self.require(name).to_dict()

	async def get_all(self) -> list[dict]:
		return [op.to_dict() for op in self.dapi.db.query(OperatorRecord).all()]

	async def get_operator_sources(self) -> list[str]:
		return [op['name'] for op in await self.get_all()]

	async def delete(self, name: str) -> None:
		record = self.require(name)
		self.dapi.db.delete(record)
		self.dapi.db.commit()

	async def delete_all(self) -> None:
		'''Delete all restricted operators.'''
		try:
			self.dapi.db.query(OperatorRecord)             \
				.filter(OperatorRecord.restrict.is_(True)) \
				.delete(synchronize_session=False)
			self.dapi.db.commit()
		except Exception as e:
			if 'database is locked' in str(e):
				raise RuntimeError('❌ SQLite database is locked. Close other connections or wait.')
			else:
				raise

	############################################################################

	async def register_plugin_operators(self):
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

	def generate_proxy_operator(self, code: str) -> str:
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
