import os, aiofiles
from datetime import datetime

from pydantic import BaseModel
from lib      import Operator, O


LOG_PATH = os.path.join(
	os.environ.get('PROJECT_PATH'),
	os.environ.get('LOG_DIR')
)


class Log(Operator):
	'''Appends a log line with timestamp to a file asynchronously. Can clear file before writing.'''

	class InputType(O):
		name  : str
		line  : str
		clear : bool = False

	class OutputType(O):
		result : bool

	async def invoke(self, name, line, clear=False):
		filepath = os.path.join(LOG_PATH, f'{name}.log')

		# Determine mode
		mode = 'w' if clear else 'a'

		# Format timestamp and line
		timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		log_line  = f'[{timestamp}] {line}\n'

		# Write line asynchronously with proper mode
		async with aiofiles.open(filepath, mode, encoding='utf-8') as f:
			await f.write(log_line)

		return True
