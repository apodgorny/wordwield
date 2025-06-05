import os, inspect
import importlib.util, importlib
from pathlib import Path
from typing  import Type


class Module:
	@staticmethod
	def import_module(module_name: str, file_path: str):
		'''
		Load and return a Python module from a file.

		Args:
			module_name: symbolic name (used for internal reference)
			file_path: absolute path to the .py file

		Returns:
			Loaded module object

		Usage:
			mod = Module.import_module('summarizer', 'app/tools/summarizer.py')
		'''
		if not os.path.exists(file_path):
			raise FileNotFoundError(f'Module file does not exist: "{file_path}"')

		spec = importlib.util.spec_from_file_location(module_name, file_path)
		if not spec or not spec.loader:
			raise ImportError(f'Cannot import module from: "{file_path}"')

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)

		return module

	@staticmethod
	def import_class(class_name: str, file_path: str):
		'''
		Import a class by name from a Python module.

		Args:
			class_name: class to extract
			file_path: absolute path to the .py file

		Returns:
			Class object

		Usage:
			cls = Module.import_class('SummarizerTool', 'app/tools/summarizer.py')
		'''
		module_name = Path(file_path).stem
		module      = Module.import_module(module_name, file_path)

		if not hasattr(module, class_name):
			raise AttributeError(f'Module "{file_path}" does not contain class "{class_name}"')

		return getattr(module, class_name)

	@staticmethod
	def find_class_by_base(base_class: Type, file_path: str):
		'''
		Find and return the first class in the module that subclasses `base_class`.

		Args:
			base_class: the base class to match
			file_path: path to the Python file

		Returns:
			Class object or None if not found

		Usage:
			cls = Module.find_class_by_base(Tool, 'app/tools/summarizer.py')
		'''
		module_name = Path(file_path).stem
		module      = Module.import_module(module_name, file_path)

		for _, obj in inspect.getmembers(module, inspect.isclass):
			if issubclass(obj, base_class) and obj is not base_class:
				return obj

		return None

	@staticmethod
	def get_exports(file_path: str) -> list[str]:
		'''
		Return `__all__` list from a module, or empty list if undefined.

		Args:
			file_path: path to an __init__.py file or module

		Returns:
			List of exported names

		Usage:
			names = Module.get_exports('app/tools/__init__.py')
		'''
		module_name = Path(file_path).stem
		module = Module.import_module(module_name, file_path)
		return getattr(module, '__all__', [])

	@staticmethod
	def load_package_classes(base_class: Type, package_path: str) -> dict[str, Type]:
		'''
		Discover and load all classes in a package directory that subclass `base_class`.

		- If __init__.py defines `__all__`, only those modules are loaded.
		- Otherwise, loads all *.py files in the directory.

		Args:
			base_class: required base class for filtering
			package_path: path to the package directory (e.g., 'app/tools')

		Returns:
			Dict of { module_name: class }

		Usage:
			registry = Module.load_package_classes(Tool, 'app/tools')
		'''
		path       = Path(package_path).resolve()
		init_path  = path / '__init__.py'
		registry   = {}

		if init_path.exists():
			exports = Module.get_exports(str(init_path))
		else:
			exports = [p.stem for p in path.glob('*.py') if p.name != '__init__.py']

		for name in exports:
			file_path = path / f'{name}.py'
			cls       = Module.find_class_by_base(base_class, str(file_path))
			if cls:
				registry[name] = cls

		return registry

	def get_module_text(module_name):
		module = importlib.import_module(module_name)
		path   = inspect.getfile(module)

		with open(path, 'r', encoding='utf-8') as f:
			return f.read()
