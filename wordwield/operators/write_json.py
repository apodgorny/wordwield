import json, os, aiofiles

from pydantic import BaseModel

from lib import Operator, O


DATA_PATH = os.path.join(
	os.environ.get('PROJECT_PATH'),
	os.environ.get('DATA_DIR')
)

class WriteJson(Operator):
	class InputType(O):
		filename : str
		data     : dict

	class OutputType(O):
		result : bool

	async def invoke(self, filename, data):
		filepath = os.path.join(DATA_PATH, filename)
		async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
			json_str = json.dumps(data, indent=2, ensure_ascii=False)
			await f.write(json_str)
		return True

