from fastapi.responses import PlainTextResponse

from wordwield.lib              import Dapi, ExecutionContext
from wordwield.services  import DefinitionService, RuntimeService, TypeService
from wordwield.schemas   import (
	NameSchema,
	EmptySchema,
	StatusSchema,
	TypeSchema,
	OperatorSchema,
	OperatorsSchema,
	OutputSchema
)

dapi = Dapi(
	TypeService,
	DefinitionService,
	RuntimeService,
)


# DEFINITION endpoints
############################################################################

@dapi.router.post('/create_type',                     response_model=TypeSchema)
@dapi.router.post('/create_type/{type_name}',         response_model=TypeSchema)
async def create_type(input: TypeSchema):
	await dapi.type_service.create(input)
	return input

@dapi.router.post('/create_operator',                 response_model=OperatorSchema)
@dapi.router.post('/create_operator/{operator_name}', response_model=OperatorSchema)
async def create_operator(input: OperatorSchema):
	name = await dapi.definition_service.create(input, replace=True)
	return await dapi.definition_service.get(name)

@dapi.router.post('/get_operator',                    response_model=OperatorSchema)
@dapi.router.post('/get_operator/{operator_name}',    response_model=OperatorSchema)
async def get_operator(input: NameSchema):
	return await dapi.definition_service.get(input.name)

@dapi.router.post('/get_all_operators',               response_model=OperatorsSchema)
async def get_all_operators(input: EmptySchema):
	records = await dapi.definition_service.get_all()
	return OperatorsSchema(items=records)

@dapi.router.post('/delete_operator',                 response_model=StatusSchema)
@dapi.router.post('/delete_operator/{operator_name}', response_model=StatusSchema)
async def delete_operator(input: NameSchema):
	await dapi.definition_service.delete(input.name)
	return {'status': 'success'}

@dapi.router.post('/reset',                           response_model=StatusSchema)
async def reset_operators(input: EmptySchema):
	await dapi.definition_service.delete_all()
	return { 'status' : 'success' }

# RUNTIME invoke
############################################################################

@dapi.router.post('/{operator_name}',                  include_in_schema=False)
@dapi.router.post('/{operator_name}/{operator_name1}', include_in_schema=False)
async def dynamic_operator_handler(operator_name: str, input: dict):
	context = ExecutionContext()
	result  = await dapi.runtime_service.invoke(operator_name, input, context)
	return OutputSchema(output=result if isinstance(result, dict) else {})
