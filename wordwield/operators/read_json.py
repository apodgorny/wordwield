import json, os

from pydantic import BaseModel

from lib import Operator, O


DATA_PATH = os.path.join(
	os.environ.get('PROJECT_PATH'),
	os.environ.get('DATA_DIR')
)

class ReadJson(Operator):
	class InputType(O):
		filename : str

	class OutputType(O):
		data : dict

	async def invoke(self, filename):
		filepath = os.path.join(DATA_PATH, filename)
		async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
			content = await f.read()
			data    = json.loads(content)
		print(type(data))
		return data

