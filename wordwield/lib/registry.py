import os, inspect, sys


class ExpertiseRegistry:
	def __init__(self, folder):
		self._folder = folder
		self._items  = {}
		self._load(folder)

	def _load(self, current):
		for entry in os.listdir(current):
			path = os.path.join(current, entry)
			if os.path.isdir(path):
				sub = ExpertiseRegistry(path)
				setattr(self, entry, sub)
				self._items[entry] = sub
			elif entry.endswith('.md') or entry.endswith('.txt'):
				name = os.path.splitext(entry)[0]
				with open(path, 'r', encoding='utf-8') as f:
					content = f.read()
				setattr(self, name, content)
				self._items[name] = content

	def __getitem__(self, key):
		return self._items[key]

	def all(self):
		return self._items

	def to_dict(self):
		result = {}
		for k, v in self._items.items():
			if isinstance(v, ExpertiseRegistry):
				result[k] = v.to_dict()
			else:
				result[k] = f'{len(v)} chars'  # You may want to return content or True/False for existence, up to you
		return result
	

class Registry:
	def __init__(self, ww, namespace=''):
		self._items     = {}  # name -> (cls, origin)
		self._ww        = ww
		self._namespace = namespace  # e.g. 'operators', 'operators.nlp'

	def register(self, cls, origin):
		name = cls.__name__
		self._items[name] = (cls, origin)
		setattr(self, name, cls)
		cls.ww = self._ww
		cls.ns = self._namespace if self._namespace else name
		cls.origin = origin  # optional, useful for reflection
		return cls

	def subregistry(self, name):
		ns  = f'{self._namespace}.{name}' if self._namespace else name
		reg = Registry(self._ww, ns)
		setattr(self, name, reg)
		self._items[name] = reg
		reg._namespace   = ns
		return reg

	def __getitem__(self, name):
		val = self._items[name]
		if isinstance(val, tuple):
			return val[0]
		return val
	
	def __getattr__(self, name):
		if name in self._items:
			val = self._items[name]
			if isinstance(val, tuple):
				return val[0]
			return val
		print(self._items)
		raise AttributeError(f'Registry `ww.{self._namespace}` has no item `{name}`')

	def all(self):
		return [v[0] if isinstance(v, tuple) else v for v in self._items.values()]

	def to_dict(self):
		result = {}
		for k, v in self._items.items():
			if isinstance(v, Registry):
				result[k] = v.to_dict()
			elif isinstance(v, tuple):
				cls, origin = v
				tag = f' ({origin})' if origin else ''
				result[k] = f'{cls.__module__}.{cls.__qualname__}{tag}'
			elif hasattr(v, '__module__') and hasattr(v, '__qualname__'):
				result[k] = f'{v.__module__}.{v.__qualname__}'
			else:
				result[k] = str(type(v))
		return result
