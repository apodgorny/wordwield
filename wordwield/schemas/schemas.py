from pydantic import BaseModel, RootModel, Field, constr
from datetime import datetime
from typing   import Any, Dict, List, Literal
from enum     import Enum

from wordwield.lib.o    import O


# Generic schemas
###########################################################################

class StatusSchema(O):
	status: str = Field(..., description='Operation status message')

class NameSchema(O):
	name: str = Field(..., description='Entity name')

class EmptySchema(O):
	pass

class OutputSchema(O):
	output: Dict[str, Any]


class TypeSchema(O):
	name        : str             = Field(...,                  description='Type name and class name (identical)')
	code        : str             = Field(...,                  description='Python code that defines the type')
	description : str             = Field('',                   description='Human‑readable description')

class OperatorSchema(O):
	name        : str             = Field(...,                  description='Operator name')
	class_name  : str             = Field(...,                  description='Class name of operator')
	input_type  : Dict[str, Any]  = Field(...,                  description='Input type name')
	output_type : Dict[str, Any]  = Field(...,                  description='Output type name')
	code        : str | None      = Field(None,                 description='Executable code (ignored for functions)')
	description : str             = Field('',                   description='Human‑readable description')
	scope       : Dict[str, Any]  = Field(default_factory=dict, description='Runtime scope for function operators')
	config      : Dict[str, Any]  = Field(default_factory=dict, description='Configuration passed to interpreter')
	restrict    : bool            = Field(default=True,         description='If True, apply interpreter restrictions')

class OperatorsSchema(O):
	items: List[OperatorSchema]