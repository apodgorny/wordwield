import os, inspect, sys
from wordwield.lib import T


class RegistryItem:
	def __init__(self, value, info=None):
		self.value = value
		self.info = info or {}

	def __str__(self):
		return f'<RegistryItem {type(self.value).__name__}>'

	def __repr__(self):
		return str(self)
	

class TextRegistryItem(RegistryItem):
	def __str__(self):
		line_count = len(self.value.splitlines())
		return f'<Text: {line_count} lines>'

	def __repr__(self):
		return str(self)


class ClassRegistryItem(RegistryItem):
	def __str__(self):
		tag = '(' + ','.join([v for k,v in self.info.items()]) + ')'
		if hasattr(self.value, '__module__') and hasattr(self.value, '__qualname__'):
			return f'{self.value.__module__}.{self.value.__qualname__}{tag}'
		return str(type(self.value))

	def __repr__(self):
		return str(self)
	

class Registry:
	def __init__(self, ns='', owner=None, fields=None):
		if owner:
			if hasattr(owner, ns) and getattr(owner, ns) is not None:
				raise RuntimeError(f'Could not attach registry `{ns}` to `{str(owner)}`. Attribute `{ns}` already exists and is not None.')
			else:
				setattr(owner, ns, self)

		self._allowed_fields = fields
		self._items          = {}
		self._ns             = ns

	def __getitem__(self, name):
		# Dotted notation
		if '.' in name:
			parts = name.split('.')
			reg = self
			for part in parts[:-1]:
				reg = reg._items.get(part)
				if reg is None or not isinstance(reg, Registry):
					raise AttributeError(f'Registry `ww.{self._ns}` has no subregistry `{part}`')
			name = parts[-1]
			return reg[name]
		
		# Regular notation: no dot
		if name in self._items:
			if isinstance(self._items[name], Registry):
				return self._items[name]
			elif isinstance(self._items[name], RegistryItem):
				return self._items[name].value
			return self._items[name]
		raise AttributeError(f'Registry `ww.{self._ns}` has no item `{name}`')

	def __getitem__(self, name):
		if name in self._items:
			if isinstance(self._items[name], Registry):
				return self._items[name]
			elif isinstance(self._items[name], RegistryItem):
				return self._items[name].value
			return self._items[name]
		raise AttributeError(f'Registry `ww.{self._ns}` has no item `{name}`')
	
	def __setitem__(self, name, value):
		if self._allowed_fields is None or name in self._allowed_fields:
			self._items[name] = value
		else:
			raise KeyError(f'Field name `{name}` is not allowed in registry `{self._ns}`.')
		return value

	def __getattr__(self, name):
		if name.startswith('_'):
			raise AttributeError(name)
		return self[name]

	def __setattr__(self, name, value):
		if name.startswith('_'):
			object.__setattr__(self, name, value)
		else:
			self[name] = value
	
	def __contains__(self, name):
		return name in self._items
	
	def __iter__(self):
		for key in self._items:
			yield self[key]

	def __str__(self):
		return T(T.DATA, T.TREE, self.to_dict())
	
	# ==========================================================
	# PUBLIC METHODS
	# ==========================================================
	
	def subregistry(self, name):
		ns = f'{self._ns}.{name}' if self._ns else name
		reg = Registry(ns)
		self._items[name] = reg
		reg._ns = ns
		return reg

	def get(self, name, default=None):
		if name in self._items:
			return self[name]
		return default

	def all(self):
		return [self[name] for name in self._items]
	
	def values(self):
		for v in self:
			yield v

	def items(self):
		for k in self._items:
			yield k, self[k]

	def keys(self):
		for k in self._items:
			yield k

	def update(self, d):
		for k in d:
			self[k] = d[k]

	def to_dict(self, cast_to_str=False, sort=1, sort_by_key=True):
		result = {}
		items = list(self._items.items())

		if sort != 0:
			reverse = sort < 0
			def key_func(pair):
				k, item = pair
				if sort_by_key:
					return k
				try:
					return str(item) if cast_to_str else item
				except Exception:
					return str(item)
			items.sort(key=key_func, reverse=reverse)

		for k, item in items:
			if isinstance(item, Registry):
				result[k] = item.to_dict(cast_to_str=cast_to_str, sort=sort, sort_by_key=sort_by_key)
			else:
				if cast_to_str:
					result[k] = str(item)
				else:
					result[k] = item
		return result
	
	def get_ns(self):
		return self._ns
