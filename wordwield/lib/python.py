import ast, types, linecache, builtins
from typing import Callable, Awaitable, Any, Dict, List, Optional
from .execution_context import ExecutionContext


class Python:
	BLOCKED_CALLS   = {'eval', 'exec', 'getattr', 'setattr', '__import__'}
	BLOCKED_ATTRS   = {'__dict__', '__class__', '__globals__', '__code__'}
	BLOCKED_GLOBALS = [
		'__import__', 'eval', 'exec', 'open', 'compile', 'globals', 'locals',
		'vars', 'getattr', 'setattr', 'delattr', 'super', 'object', 'dir'
	]
	ALLOWED_GLOBALS = {
		'print'      : print,
		'range'      : range,
		'enumerate'  : enumerate,
		'len'        : len,
		'isinstance' : isinstance,
		'exit'       : exit,
		'zip'        : zip,
		'sum'        : sum,
		'min'        : min,
		'max'        : max,

		'type'       : type,
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
		'Optional'   : Optional,
		'Any'        : Any,
		'Callable'   : Callable,
		'Awaitable'  : Awaitable,
		
		'property'   : property,

		'__builtins__' : {
			'__build_class__': builtins.__build_class__,
			'__name__'       : builtins.__name__
		}
	}

	def __init__(
		self,
		execution_context      : Optional[ExecutionContext],
		registered_operators   : set,
		extra_globals          : dict,
		call_external_operator : Callable[[str, dict, ExecutionContext], Awaitable[Any]],
		restrict               : bool = True
	):
		self.call_external_operator = call_external_operator
		self.execution_context      = execution_context
		self.registered_operators   = registered_operators
		self.globals                = extra_globals
		self.locals                 = {}
		self.i                      = execution_context.i
		self.restrict               = restrict
		self.filename               = f'<not set>'

	############################################################################

	async def _initialize(self, entity_name, code):
		self.env_stack = []
		self.filename  = f'<{entity_name}>'
		self.globals['_wrap_call_async'] = self._wrap_call_async

		compiled = self._compile(code)
		exec(compiled, self.globals, self.locals)

	############################################################################

	def _apply_restrictions(self, tree):
		for name in Python.BLOCKED_GLOBALS:
			self.globals[name] = None
		self.globals.update(Python.ALLOWED_GLOBALS)
		self._detect_dangerous_calls(tree)

	def _detect_dangerous_calls(self, tree: ast.AST):
		class DangerousCallDetector(ast.NodeVisitor):
			def visit_Import(self, node):
				raise ValueError('Use of `import` is not allowed')

			def visit_ImportFrom(self, node):
				raise ValueError('Use of `from ... import` is not allowed')

			def visit_Call(self, node):
				if isinstance(node.func, ast.Name) and node.func.id in Python.BLOCKED_CALLS:
					raise ValueError(f'Use of `{node.func.id}` is not allowed')
				self.generic_visit(node)

			def visit_Attribute(self, node):
				if node.attr in Python.BLOCKED_ATTRS:
					raise ValueError(f'Access to `{node.attr}` is not allowed')
				self.generic_visit(node)

		DangerousCallDetector().visit(tree)

	############################################################################

	def _compile(self, code: str) -> types.CodeType:
		tree = ast.parse(code, filename=self.filename)

		if self.restrict:
			self._apply_restrictions(tree)

		class CallRewriter(ast.NodeTransformer):
			def __init__(self, globals, registered_operators):
				super().__init__()
				self.globals              = globals
				self.registered_operators = registered_operators

			def visit_Call(self, node: ast.Call) -> ast.AST:
				self.generic_visit(node)
				if isinstance(node.func, ast.Name):
					if node.func.id in self.globals:
						return node # skip rewriting known globals like call, ask, print

					if not node.func.id in self.registered_operators:
						raise NameError(f'Unknown identifier `{node.func.id}`: is not in globals and not a registered operator')

					return ast.copy_location(ast.Call(
						func = ast.Name(id='_wrap_call_async', ctx=ast.Load()),
						args = [
							ast.Constant(node.func.id),
							ast.List(elts=node.args, ctx=ast.Load()),
							ast.Dict(
								keys   = [ast.Constant(kw.arg) for kw in node.keywords if kw.arg],
								values = [kw.value for kw in node.keywords if kw.arg]
							),
							ast.Constant(node.lineno)
						],
						keywords = []
					), node)
				return node

		# 🔧 применяем AST преобразования
		tree = CallRewriter(self.globals, self.registered_operators).visit(tree)
		ast.fix_missing_locations(tree)

		# 🔥 добавляем код в linecache под псевдо-именем
		linecache.cache[self.filename] = (
			len(code),
			None,
			code.splitlines(True),
			self.filename
		)
		return compile(tree, filename=self.filename, mode='exec')

	############################################################################

	async def _wrap_call_async(self, name: str, args_list: list[Any], kwargs_dict: dict, line: int) -> Any:
		self.execution_context.push(name, line)
		try:
			return await self.call_external_operator(
				name, args_list, kwargs_dict, self.execution_context
			)
		finally:
			self.execution_context.pop()

	############################################################################

	async def invoke(
		self,
		operator_name          : str,
		operator_class_name    : str,
		input_dict             : dict,
		code                   : str,
	):
		await self._initialize(operator_name, code)
		self.execution_context.push(operator_name, 1, 'restricted' if self.restrict else 'unrestricted')
		try:
			operator_class = self.locals.get(operator_class_name)
			if not operator_class:
				raise ValueError(f'Class `{operator_class_name}` not found')

			instance = operator_class(operator_name, self.globals)
			invoke_method = getattr(instance, 'invoke', None)
			if not invoke_method:
				raise ValueError(f'Method `invoke` not found in `{operator_class_name}`')

			return await invoke_method(**input_dict)
		finally:
			self.execution_context.pop()

	############################################################################

	async def eval_type(self, code: str, class_name: str, get_external_type, context) -> type:
		while True:
			try:
				await self._initialize(class_name, code)
				if class_name not in self.locals:
					raise ValueError(f'Class `{class_name}` not defined in code.')
				return self.locals[class_name]
			except NameError as e:
				missing_type = getattr(e, 'name', None)
				if not missing_type:
					raise

				external_type = await get_external_type(missing_type, context)
				self.globals[missing_type] = external_type