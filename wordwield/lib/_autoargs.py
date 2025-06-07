'''
autoargs.py

Provides utilities for automatically filtering and injecting function arguments
based on signature — especially useful for methods inside dynamically invoked
plugin operators or agent frameworks.

Included:

- autoargs:     Decorator that auto-selects only matching keyword arguments.
- autodecorate: Utility to decorate specific methods on an object.
- resolve_signature_args: Converts (*args, **kwargs) to filtered kwargs based on a function's signature.

These tools are intended to simplify operator chaining, signature-safe dispatch,
and passing large shared context dicts into only the relevant parameters.
'''

import inspect
import asyncio
from types import MethodType
from typing import Callable


def autoargs(func: Callable) -> Callable:
	'''
	Decorator that filters keyword arguments to only those declared in the method signature.
	Works for both sync and async methods.

	Useful when calling methods with large shared context dictionaries.

	Example:
		@autoargs
		async def invoke(self, x, y): ...

		await operator.invoke(x=1, y=2, extra='ignored')
	'''
	is_async = asyncio.iscoroutinefunction(func)

	async def async_wrapper(self, *args, **kwargs):
		sig     = inspect.signature(func)
		params  = sig.parameters
		usable  = {k: v for k, v in kwargs.items() if k in params}
		return await func(self, *args, **usable)

	def sync_wrapper(self, *args, **kwargs):
		sig     = inspect.signature(func)
		params  = sig.parameters
		usable  = {k: v for k, v in kwargs.items() if k in params}
		return func(self, *args, **usable)

	return async_wrapper if is_async else sync_wrapper


def autodecorate(obj: object, method_names: list[str], decorator=autoargs) -> None:
	'''
	Applies the given decorator to specified methods on an instance.
	By default uses `autoargs`, but can be used with any method-compatible decorator.

	Example:
		class Operator:
			def __init__(self):
				autodecorate(self, ['invoke'])

			async def invoke(self, x, y): ...

		operator = Operator()
		await operator.invoke(x=1, y=2, z='ignored')
	'''
	for name in method_names:
		method  = getattr(obj, name)
		raw     = method.__func__ if hasattr(method, '__func__') else method
		wrapped = decorator(raw)
		setattr(obj, name, MethodType(wrapped, obj))


def resolve_signature_args(func: Callable, args: tuple, kwargs: dict) -> dict:
	'''
	Converts positional and keyword arguments into a filtered kwargs dictionary
	based on the target function's signature.

	Used when you want to dynamically call a function using both *args and **kwargs,
	but only include parameters that the function declares.

	Example:
		def greet(name, mood): ...
		args = ('Alice',)
		kwargs = {'mood': 'happy', 'extra': 'ignored'}

		filtered = resolve_signature_args(greet, args, kwargs)
		# → { 'name': 'Alice', 'mood': 'happy' }
	'''
	sig     = inspect.signature(func)
	params  = list(sig.parameters.keys())
	pos_map = {k: v for k, v in zip(params, args)}
	return {
		**pos_map,
		**{k: v for k, v in kwargs.items() if k in params}
	}
