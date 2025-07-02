import types

from pydantic.fields import FieldInfo

from .predicates     import is_annotation, get_default


class OField(FieldInfo):
	def __init__(self, *args, default=None, default_factory=None, description='', **kwargs):
		extra = kwargs.pop('json_schema_extra', {}) or {}
		if description:
			extra['description']  = description
			kwargs['description'] = description

		self._type = None
		if args:
			if is_annotation(args[0]):
				args = list(args)
				self._type = args.pop()
		if args:
			raise RuntimeError(f'OField: Unexpected positional args: {args}')

		# Pass all non-service kwargs into extra
		for k, v in dict(kwargs).items():
			if not (isinstance(v, type) or isinstance(v, types.FunctionType)):
				extra[k] = v
			if k not in ['default', 'default_factory', 'description']:
				kwargs.pop(k)

		init_kwargs = {'json_schema_extra': extra}

		# Correct logic for defaults:
		if default is not None:
			init_kwargs['default'] = default
		elif default_factory is not None:
			init_kwargs['default_factory'] = default_factory
		elif self._type is not None:
			def_val = get_default(self._type)
			# Use default_factory for mutable types, default for everything else
			if isinstance(def_val, (list, dict, set)):
				init_kwargs['default_factory'] = lambda: get_default(self._type)
			else:
				init_kwargs['default'] = def_val

		super().__init__(**init_kwargs)

	@property
	def extra(self):
		return self.json_schema_extra or {}

	def get_type(self):
		return getattr(self, '_type', None)

	def get_default(self, *args, **kwargs):
		# Совместимость с Pydantic: всегда возвращаем дефолт или фабрику
		if getattr(self, 'default', None) is not None:
			return self.default
		if getattr(self, 'default_factory', None) is not None:
			return self.default_factory()
		return ...
