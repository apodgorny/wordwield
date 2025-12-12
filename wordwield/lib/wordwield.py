import os, sys, asyncio, shutil, yaml
from dotenv import dotenv_values

from sqlalchemy                  import create_engine, inspect, text
from sqlalchemy.orm              import sessionmaker
from wordwield.lib.base.record   import Base, Record
from wordwield.lib.base          import Service
from wordwield.lib.fs            import Directory, File

from wordwield.lib import (
	Operator,
	Module,
	O,
	T,
	Model,
	Registry,
	ClassRegistryItem,
	TextRegistryItem,
	String
)

# Runs coroutines synchronously so `ww(...)` executes without explicit await.
# ------------------------------------------------------------------
class WordWieldMeta(type):
	def __call__(cls, coroutine, *args, **kwargs):
		return asyncio.run(coroutine)

# ------------------------------------------------------------------
class WordWield(metaclass=WordWieldMeta):
	verbose        = True
	is_initialized = False
	operators      = None
	schemas        = None
	models         = None
	env            = None

	# Initialize WordWield framework for given project.
	# ------------------------------------------------------------------
	@classmethod
	def init(cls, PROJECT_NAME, PROJECT_PATH, reset_db=True, verbose=True):
		cls.verbose = verbose
		# Create top-level registries on the WordWield singleton.
		Registry('env',       cls)
		Registry('config',    cls)
		Registry('operators', cls)
		Registry('schemas',   cls)
		Registry('models',    cls)
		Registry('expertise', cls)
		Registry('services',  cls)

		# Load environment variables from root and project .env into env registry.
		cls._setup_env(PROJECT_NAME, PROJECT_PATH)
		
		# Resolve paths, prepare DB, and load built-in + project classes.
		cls._setup_paths(PROJECT_NAME, PROJECT_PATH)

		cls._register_builtins()
		cls._register_project()

		cls._init_db(drop_existing=reset_db)
		cls._init_services()

		cls.is_initialized = True
		cls.log_success(f"Project '{PROJECT_NAME}' initialized in '{PROJECT_PATH}'")
		cls.log(T(T.DATA, T.TREE, cls.to_dict(), f'Project `{cls.config.PROJECT_NAME}`', color=True))

	# Load environment from WordWield root .env with project .env overrides.
	# ------------------------------------------------------------------
	@classmethod
	def _setup_env(cls, project_name, project_path):
		# Load env files in priority order: repo root → wordwield/ → project
		lib_root       = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
		repo_root_env  = os.path.abspath(os.path.join(lib_root, '..', '.env'))
		lib_env_path   = os.path.join(lib_root, '.env')
		project_env    = os.path.join(project_path, '.env')

		env = {}
		for path in (repo_root_env, lib_env_path, project_env):
			if os.path.isfile(path):
				env.update({k: v for k, v in dotenv_values(path).items() if v is not None})

		# Apply defaults then update env registry
		if not env.get('DB_NAME'):
			env['DB_NAME'] = project_name
		cls.env.update(env)

	# Setup key project paths into config registry.
	# ------------------------------------------------------------------
	@classmethod
	def _setup_paths(cls, PROJECT_NAME, PROJECT_PATH):
		# Persist key paths so registries and DB know where to read/write.
		cls.config['PROJECT_NAME']       = PROJECT_NAME
		cls.config['PROJECT_PATH']       = PROJECT_PATH
		cls.config['EXPERTISE_FILE_EXT'] = File.READABLE_FILE_EXT

		# Framework root (built-in operators/schemas/models live here).
		cls.config['WW_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

		# Compute DB file path inside the project dir.
		db_name = cls.env.get('DB_NAME', PROJECT_NAME)
		db_file = os.path.abspath(os.path.join(PROJECT_PATH, f'{db_name}.db'))
		cls.config['DB_PATH'] = db_file

		# Ensure project subdirs exist and store their paths.
		dir_vars = [
			('OPERATORS_DIR', 'operators'),
			('SCHEMAS_DIR',   'schemas'),
			('MODELS_DIR',    'models'),
			('LOGS_DIR',      'logs'),
			('EXPERTISE_DIR', 'expertise'),
		]
		for key, default in dir_vars:
			dir_name = cls.env.get(key, default)
			abs_path = os.path.join(PROJECT_PATH, dir_name)
			os.makedirs(abs_path, exist_ok=True)
			cls.config[key] = abs_path
		
		# Fresh log directory each init.
		shutil.rmtree(cls.config.LOGS_DIR)
		os.makedirs(cls.config.LOGS_DIR, exist_ok=True)

	# Register all built-in classes into registries.
	# ------------------------------------------------------------------
	@classmethod
	def _register_builtins(cls):
		# Walk the framework-provided packages and register any subclasses of the expected bases.
		cls._register_class(os.path.join(cls.config.WW_PATH, 'schemas'),   cls.schemas,   O)
		cls._register_class(os.path.join(cls.config.WW_PATH, 'operators'), cls.operators, Operator)
		cls._register_class(os.path.join(cls.config.WW_PATH, 'models'),    cls.models,    Model)
		cls._register_class(os.path.join(cls.config.WW_PATH, 'services'),  cls.services,  Service)

	# Register all project-specific classes into registries.
	# ------------------------------------------------------------------
	@classmethod
	def _register_project(cls):
		# Walk the project packages and register subclasses alongside their namespaces.
		cls._register_class(cls.config.SCHEMAS_DIR,   cls.schemas,   O,        cls.config.PROJECT_NAME)
		cls._register_class(cls.config.OPERATORS_DIR, cls.operators, Operator, cls.config.PROJECT_NAME)
		cls._register_class(cls.config.MODELS_DIR,    cls.models,    Model,    cls.config.PROJECT_NAME)

		 # Load expertise files into the expertise registry.
		cls._register_expertise(cls.config.EXPERTISE_DIR, cls.expertise)

	# Compile list of Python files to inspect for subclasses.
	# ------------------------------------------------------------------
	@classmethod
	def _compile_import_file_list(cls, package_path, registry, base_class, origin='wordwield'):
		import_list  = []
		package_path = os.path.abspath(package_path)

		if not os.path.isdir(package_path):
			return []

		# Add each .py file except __init__.py
		for fname in os.listdir(package_path):
			fpath = os.path.join(package_path, fname)
			if os.path.isfile(fpath) and fname.endswith('.py') and fname != '__init__.py':
				import_list.append({
					'file'       : fpath,
					'registry'   : registry,
					'base_class' : base_class,
					'origin'     : origin
				})

		# Recurse into subfolders
		for entry in os.listdir(package_path):
			subdir = os.path.join(package_path, entry)
			if os.path.isdir(subdir) and not entry.startswith('__'):
				subreg = registry.subregistry(entry)
				import_list.extend(cls._compile_import_file_list(subdir, subreg, base_class, origin))
		return import_list
	
	# Register expertise files from given path into given registry.
	# ------------------------------------------------------------------
	@classmethod
	def _register_expertise(cls, path, reg):
		def on_subdirectory(d):
			subreg = reg.subregistry(d.name)
			cls._register_expertise(d.path, subreg)

		def on_file(f):
			reg[f.prefix] = TextRegistryItem(f.read())

		Directory(path).walk(
			on_subdirectory = on_subdirectory,
			on_file         = on_file,
			extensions      = cls.config.EXPERTISE_FILE_EXT,
			recursive       = False
		)

	# Register all classes found in package path into given registry.
	# ------------------------------------------------------------------
	@classmethod
	def _register_class(cls, package_path, registry, base_class, origin='wordwield'):
		file_list = cls._compile_import_file_list(package_path, registry, base_class, origin)
		remaining = list(file_list)
		n_passes = 0

		while remaining:
			error     = None
			n_passes += 1
			progress  = False
			for item in remaining[:]:
				fpath = item['file']
				reg   = item['registry']
				base  = item['base_class']
				orig  = item['origin']
				try:
					classes = Module.find_all_classes_by_base(base, fpath)
					if classes:
						for klass in classes:
							# Attach namespace and ww handle, then stash class in registry with origin info.
							setattr(klass, 'ns', reg.get_ns())
							klass.ww = cls
							reg[klass.__name__] = ClassRegistryItem(klass, {'origin': orig})
					remaining.remove(item)
					progress = True
				except Exception as e:
					error = e
					remaining.remove(item)
					remaining.append(item)
			if not progress:
				raise error
			
	# Initialize all registered services
	# ------------------------------------------------------------------
	@classmethod
	def _init_services(cls):
		for name, service in cls.services.items():
			cls.log_info(f'Initializing service: `{name}`')
			service()
		cls.log_success(f'Services initialized')

	# Initialize or reset DB engine/session and create all tables.
	# If drop_existing is True, drop all tables but do NOT delete the db file.
	# ------------------------------------------------------------------
	@classmethod
	def _init_db(cls, drop_existing=False):
		db_path = cls.config.get('DB_PATH') or cls.config.get('DB_FILE')
		db_url  = f'sqlite:///{db_path}'

		# Ensure directory is writable
		parent_dir = os.path.dirname(db_path) or '.'
		if not os.access(parent_dir, os.W_OK):
			raise RuntimeError(f'❌ Cannot create DB file: Directory `{parent_dir}` is not writable.')

		# Create SQLAlchemy engine/session and wire persistence helpers on O.
		engine = create_engine(db_url, connect_args={'check_same_thread': False}, echo=False)
		Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
		session = Session()

		cls.engine = engine
		cls.db     = session
		Record.session = session
		O.enable_persistence(session)
		O.enable_instantiation(cls.get_operator_class)

		if drop_existing:
			# --- Drop all tables, but do NOT remove the file ---
			inspector = inspect(engine)
			with engine.begin() as conn:
				for table_name in inspector.get_table_names():
					conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
			cls.log_info('All tables dropped (DB file retained)')

		# Recreate all tables from models
		Base.metadata.create_all(bind=engine)
		cls.log_success(f'Database initialized at {db_path}')

	# Resolve operator class from registry path.
	# ------------------------------------------------------------------
	@classmethod
	def get_operator_class(cls, path: str):
		'''
		Resolves operator class from registry path like:
		'MyOperator' or 'operators.MyOperator' or 'operators.nlp.Summarizer'
		'''
		parts = path.split('.')
		reg   = cls.operators

		for part in parts[:-1]:
			reg = reg.subregistry(part)

		class_name = parts[-1]
		operator_class = reg[class_name]

		if not isinstance(operator_class, type):
			raise RuntimeError(f'`{path}` did not resolve to a class (got: {type(operator_class)})')

		return operator_class

	# Logging utilities
	# ------------------------------------------------------------------
	@classmethod
	def log(cls, msg, color='') : print(msg, flush=True)
	@classmethod
	def log_success(cls, msg)   : print(String.color(f'SUCCESS:', String.GREEN, 'b'),  msg, flush=True)
	@classmethod
	def log_info(cls, msg)      : print(String.color(f'INFO:   ', String.CYAN, 'b'),      msg, flush=True)
	@classmethod
	def log_warning(cls, msg)   : print(String.color(f'WARNING:', String.YELLOW, 'b'), msg, flush=True)
	@classmethod
	def log_error(cls, msg)     : print(String.color(f'ERROR:  ', String.RED, 'b'),      msg, flush=True); raise RuntimeError(msg)
	
	# Central LLM call with schema validation.
	# ------------------------------------------------------------------
	@classmethod
	async def ask(
		cls,
		prompt,
		schema,
		model_id    = 'ollama::gemma3:4b',
		# model_id    = 'ollama::gemma3n:e4b',
		temperature = 0.0,
		verbose = None
	):
		return await Model.generate(
			ww              = cls,
			prompt          = prompt,
			response_schema = schema,
			model_id        = model_id,
			temperature     = temperature,
			verbose         = cls.verbose if verbose is None else verbose,
		)
	
	# Export current framework state as dictionary.
	# ------------------------------------------------------------------
	@classmethod
	def to_dict(cls):
		'''
		Export config and registry names (structure only, not registry contents).
		When registries implement their own to_dict, this can delegate to them.
		'''
		return {
			'config'         : cls.config.to_dict(cast_to_str=True),
			'env'            : cls.env.to_dict(cast_to_str=True), # Or cls.operators.to_dict() in the future
			'is_initialized' : cls.is_initialized,
			'verbose'        : cls.verbose,
			'operators'      : cls.operators.to_dict(cast_to_str=True), # Or cls.operators.to_dict() in the future
			'schemas'        : cls.schemas.to_dict(cast_to_str=True),   # Or cls.schemas.to_dict()
			'services'       : cls.services.to_dict(cast_to_str=True),  # Or cls.services.to_dict()
			'models'         : cls.models.to_dict(cast_to_str=True),    # Or cls.models.to_dict()
			'expertise'      : cls.expertise.to_dict(cast_to_str=True), # Or cls.expertise.to_dict()
		}
	
	##########################################################################

	
