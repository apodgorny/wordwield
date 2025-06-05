import os
from dotenv import load_dotenv

load_dotenv()


if 'CLIENT' in os.environ:
	from .string            import String
	from .highlight         import Highlight
	from .wordwield         import WordWield
	from .code              import Code

	from .o                 import O
	from .operator          import Operator
	from .agent             import Agent
	from .expert            import Expert

else:
	from .dapi              import Dapi, DapiException, DapiService
	from .python            import Python

	from .string            import String
	from .highlight         import Highlight

	from .module            import Module
	from .o                 import O
	from .model             import Model

	from .operator          import Operator
	from .agent             import Agent
	from .expert            import Expert

	from .execution_context import ExecutionContext

	from .reserved          import is_reserved
	from .autoargs          import autoargs, autodecorate
	from .jscpy             import jscpy, Jscpy

	from .edge              import Edge
	from .record            import Record
