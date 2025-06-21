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
		return f'<Text: {len(self.value.split("\n"))} lines>'

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
	def __init__(self, ns='', owner=None):
		if owner:
			if hasattr(owner, ns) and getattr(owner, ns) is not None:
				raise RuntimeError(f'Could not attach registry `{ns}` to `{str(owner)}`. Attribute already exists and is not None.')
			else:
				setattr(owner, ns, self)

		self._items = {}
		self._ns    = ns

	def subregistry(self, name):
		ns = f'{self._ns}.{name}' if self._ns else name
		reg = Registry(ns)
		self._items[name] = reg
		reg._ns = ns
		return reg

	def __getitem__(self, name):
		if name in self._items:
			if isinstance(self._items[name], Registry):
				return self._items[name]
			elif isinstance(self._items[name], RegistryItem):
				return self._items[name].value
			return self._items[name]
		raise AttributeError(f'Registry `ww.{self._ns}` has no item `{name}`')
	
	def __setitem__(self, name, value):
		self._items[name] = value
		return self

	def __getattr__(self, name):
		return self[name]
	
	def __contains__(self, name):
		return name in self._items
	
	def __iter__(self):
		for key in self._items:
			yield self[key]

	def __str__(self):
		return T(T.DATA, T.TREE, self.to_dict())

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

	def to_dict(self):
		result = {}
		for k, item in self._items.items():
			if isinstance(item, Registry):
				result[k] = item.value.to_dict()
			else:
				result[k] = item
		return result
