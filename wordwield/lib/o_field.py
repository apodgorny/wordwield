import types

from pydantic.fields import FieldInfo
from .predicates     import is_annotation


class OField(FieldInfo):
	def __init__(self, *args, description='', **kwargs):
		extra = kwargs.pop('json_schema_extra', {}) or {}
		if description:
			extra['description']  = description
			kwargs['description'] = description

		if args:
			if is_annotation(args[0]):
				args = list(args)
				self._type = args.pop()
		if args:
			raise RuntimeError(f'OField: Unexpected positional args: {args}')

		for k, v in dict(kwargs).items():
			if not (isinstance(v, type) or isinstance(v, types.FunctionType)):
				extra[k] = v
			if k not in ['default', 'default_factory', 'description']:
				kwargs.pop(k)

		super().__init__(json_schema_extra=extra, **kwargs)

	@property
	def extra(self):
		return self.json_schema_extra or {}
	
	def get_type(self):
		return getattr(self, '_type', None)
	
	def get_default(self):
		return self.default if self.default is not None else (self.default_factory if self.default_factory is not None else ...)
