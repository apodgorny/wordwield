from __future__    import annotations

import json
from typing        import Any, Dict, List, Optional

from wordwield.lib           import DapiService, DapiException, O, Python

from wordwield.db       import TypeRecord
from wordwield.schemas  import TypeSchema


@DapiService.wrap_exceptions()
class TypeService(DapiService):
	'''Stores and manages type definitions as schema + code.'''

	def _get_type_globals(self):
		return {
			'O'        : O,
			'Optional' : Optional,
			'List'     : List,
			'Dict'     : Dict
		}

	async def initialize(self):
		await super().initialize()

	async def create(self, schema: TypeSchema):
		if not schema.name:
			raise DapiException.halt('Missing type name')

		existing = self.dapi.db.get(TypeRecord, schema.name)
		if existing:
			self.dapi.db.delete(existing)

		self.dapi.db.add(TypeRecord(
			name        = schema.name,
			description = schema.description,
			code        = schema.code,
		))
		self.dapi.db.commit()

		return schema

	async def get(self, name, context) -> TypeSchema:
		extra_globals = self.dapi.runtime_service.get_globals(context)
		if name in self.dapi.odb.types:
			return self.dapi.odb.types[name]

		record = self.dapi.db.get(TypeRecord, name)
		if not record:
			raise DapiException(
				status_code = 404,
				detail      = f'Type `{name}` not found',
				severity    = 'halt'
			)
		try:
			context.push(
				name        = name,
				lineno      = 1,
				restrict    = True,
				importance  = 1
			)
			interpreter = Python(
				execution_context      = context,
				registered_operators   = await self.dapi.runtime_service.get_registered_operator_names(),
				extra_globals          = extra_globals,
				call_external_operator = self.dapi.runtime_service.call_external_operator,
				restrict               = True
			)
			loaded_type = await interpreter.eval_type(
				code              = record.code,
				class_name        = record.name,
				get_external_type = self.get,
				context           = context
			)
			self.dapi.odb.types[name] = loaded_type
			return loaded_type
		except Exception as e:
			raise DapiException.consume(e)
		finally:
			context.pop()

	async def get_all(self, context) -> list[TypeSchema]:
		classes = {}
		for (name,) in self.dapi.db.query(TypeRecord.name).all():
			classes[name] = await self.get(name, context)
		return classes		

	async def delete(self, name: str):
		record = self.dapi.db.get(TypeRecord, name)
		if record:
			self.dapi.db.delete(record)
			self.dapi.db.commit()

	async def delete_all(self):
		self.dapi.db.query(TypeRecord).delete()
		self.dapi.db.commit()
