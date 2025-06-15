import os
import sys
from dotenv import dotenv_values

from wordwield.lib import (
	Operator,
	Module,
	O,
	T,
	Model,
	Registry,
	ExpertiseRegistry
)


class WordWield:
	verbose        = True
	is_initialized = False
	config         = {}
	operators      = None
	schemas        = None
	models         = None

	@classmethod
	def init(cls, PROJECT_NAME, PROJECT_PATH):
		cls.operators = Registry(cls, 'operators')
		cls.schemas   = Registry(cls, 'schemas')
		cls.models    = Registry(cls, 'models')

		cls._setup_paths(PROJECT_NAME, PROJECT_PATH)
		cls._register_builtins()
		cls._register_project()

		cls.is_initialized = True
		cls.log_success(f"Project '{PROJECT_NAME}' initialized in '{PROJECT_PATH}'")
		cls.log_success(T(T.DATA, T.TREE, cls.to_dict(), f'Project `{cls.config["PROJECT_NAME"]}`', color=True))

	@classmethod
	def _setup_paths(cls, PROJECT_NAME, PROJECT_PATH):
		cls.config['WW_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
		env = dotenv_values(os.path.join(os.path.dirname(__file__), '.env'))

		db_name = env.get('DB_NAME', PROJECT_NAME)
		db_file = os.path.abspath(os.path.join(PROJECT_PATH, f"{db_name}.db"))
		cls.config['DB_PATH'] = db_file

		cls.config['PROJECT_NAME'] = PROJECT_NAME
		cls.config['PROJECT_PATH'] = PROJECT_PATH

		dir_vars = [
			('OPERATORS_DIR', 'operators'),
			('SCHEMAS_DIR',   'schemas'),
			('MODELS_DIR',    'models'),
			('LOGS_DIR',      'logs'),
			('EXPERTISE_DIR', 'expertise'),
		]
		for key, default in dir_vars:
			dir_name = env.get(key, default)
			abs_path = os.path.join(PROJECT_PATH, dir_name)
			os.makedirs(abs_path, exist_ok=True)
			cls.config[key] = abs_path

	@classmethod
	def _register_builtins(cls):
		cls._register(os.path.join(cls.config['WW_PATH'], 'operators'), cls.operators, Operator)
		cls._register(os.path.join(cls.config['WW_PATH'], 'schemas'),   cls.schemas,   O)
		cls._register(os.path.join(cls.config['WW_PATH'], 'models'),    cls.models,    Model)

	@classmethod
	def _register_project(cls):
		cls._register(cls.config['OPERATORS_DIR'], cls.operators, Operator, cls.config['PROJECT_NAME'])
		cls._register(cls.config['SCHEMAS_DIR'],   cls.schemas,   O,        cls.config['PROJECT_NAME'])
		cls._register(cls.config['MODELS_DIR'],    cls.models,    Model,    cls.config['PROJECT_NAME'])
		cls.expertise = ExpertiseRegistry(cls.config['EXPERTISE_DIR'])

	@classmethod
	def _register(cls, package_path, registry, base_class, origin='wordwield'):
		package_path = os.path.abspath(package_path)
		if not os.path.isdir(package_path):
			return

		init_file = os.path.join(package_path, '__init__.py')
		if not os.path.exists(init_file):
			with open(init_file, 'w', encoding='utf-8') as f:
				pass

		# Register .py files in this folder
		try:
			classes = Module.load_package_classes(base_class, package_path)
		except Exception as e:
			cls.log_error(str(e))

		if not classes:
			cls.log_info(f'No classes found in `{package_path}` for `{base_class}`')
		else:
			for klass in classes.values():
				registry.register(klass, origin)

		# Recurse into subfolders
		for entry in os.listdir(package_path):
			subdir = os.path.join(package_path, entry)
			if os.path.isdir(subdir) and not entry.startswith('__'):
				subreg = registry.subregistry(entry)
				cls._register(subdir, subreg, base_class)

	@classmethod
	def log(cls, msg, color=''):
		print(msg, flush=True)

	@classmethod
	def log_success(cls, msg):
		print(f"\033[92mSUCCESS:\033[0m {msg}", flush=True)

	@classmethod
	def log_info(cls, msg):
		print(f"\033[96mINFO:\033[0m {msg}", flush=True)

	@classmethod
	def log_error(cls, msg):
		print(f"\033[91mERROR:\033[0m {msg}", flush=True)
		exit(0)
		# raise RuntimeError(msg)
	
	@classmethod
	def log_warning(cls, msg):
		print(f"\033[93mWARNING:\033[0m {msg}", flush=True)
	
	@classmethod
	async def ask(
		prompt,
		response_model,

		model_id    = 'ollama::gemma3:4b',
		temperature = 0.0
	):
		return await Model.generate(
			prompt          = prompt,
			response_model  = response_model,
			model_id        = model_id,
			temperature     = temperature
		)
	
	@classmethod
	def to_dict(cls):
		'''
		Export config and registry names (structure only, not registry contents).
		When registries implement their own to_dict, this can delegate to them.
		'''
		return {
			'config'         : dict(cls.config),
			'is_initialized' : cls.is_initialized,
			'verbose'        : cls.verbose,
			'operators'      : cls.operators.to_dict(), # Or cls.operators.to_dict() in the future
			'schemas'        : cls.schemas.to_dict(),   # Or cls.schemas.to_dict()
			'models'         : cls.models.to_dict(),    # Or cls.models.to_dict()
			'expertise'      : cls.expertise.to_dict(), # Or cls.expertise.to_dict()
			'test_items'     : ['foo', 'bar', 'baz']
		}
