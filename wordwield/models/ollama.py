import re, json, codecs, asyncio, ollama, subprocess, time

from wordwield.lib import Model


class OllamaModel(Model):
	def __init__(self, name: str):
		self.name   = name
		self.client = ollama

	def _strip_schema(self, schema: dict) -> dict:
		'''Clean JSON Schema for Ollama compatibility.'''
		def strip(obj):
			if isinstance(obj, dict):
				return {
					k: strip(v)
					for k, v in obj.items()
					if k not in {'title', 'default', 'examples', 'definitions', '$defs'}
				}
			if isinstance(obj, list):
				return [strip(i) for i in obj]
			return obj

		return strip(schema)

	def _sanitize_output(self, output: str) -> str:
		output = re.sub(r'<0x([0-9a-fA-F]{2})>', lambda m: chr(int(m[1], 16)),                    output)
		output = re.sub(r'\\u[0-9a-fA-F]{4}',    lambda m: codecs.decode(m[0], 'unicode_escape'), output)

		try:
			return output.encode('latin1').decode('utf-8')
		except UnicodeError:
			return output

	async def __call__(
		self,
		prompt          : str,
		response_schema : dict,
		role            : str = 'user',
		temperature     : float = 0.0,
		system          : str | None = None
	) -> dict:
		# print('='*30)
		# print(response_schema)
		# print('='*30)
		params = {
			'model'    : self.name,
			'messages' : [{
				'role'    : role,
				'content' : prompt
			}],
			'format'  : self._strip_schema(response_schema),
			'options' : {
				'temperature' : temperature,
				'keep_alive'  : 60
			}
		}

		if system:
			params['messages'].insert(0, {'role': 'system', 'content': system})

		print(prompt)
		print('-' * 30)
		response = await asyncio.to_thread(self.client.chat, **params)
		print(f'✅ {self.name} returned:')
		text = response['message']['content'].strip()
		print('-' * 30)
		print(text)
		sanitized = self._sanitize_output(text)

		return json.loads(sanitized)
	
	def restart_model(self):
		print(f'\nRESTARTING ollama::{self.name} ...')
		subprocess.run(['ollama', 'unload', self.name])
		time.sleep(1)
		subprocess.run(['ollama', 'stop'])
		time.sleep(2)
		subprocess.run(['ollama', 'run', self.name, '-p', 'say hello and nothing else'])
		print('RESTART COMPLETE\n')

		
