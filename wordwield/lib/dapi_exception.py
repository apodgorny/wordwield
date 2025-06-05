import traceback
from pathlib           import Path
from fastapi.responses import JSONResponse
from pydantic          import BaseModel
from starlette.status  import HTTP_400_BAD_REQUEST


class DapiException(Exception):
	HALT   = 'halt'
	BEWARE = 'beware'
	FYI    = 'fyi'

	def __init__(
		self,
		status_code : int         = HTTP_400_BAD_REQUEST,
		detail      : str | dict  = 'An error occurred',
		severity    : str         = None,
		headers     : dict | None = None,
		context     : dict | None = None
	):
		self.status_code = status_code
		self.detail      = detail
		self.severity    = severity or self.HALT
		self.headers     = headers
		self.context     = context or {}

		self._data = self._to_serializable({
			'detail'   : self.detail,
			'severity' : self.severity,
			**self.context
		})

		super().__init__(str(self._data.get('detail', 'An error occurred')))

	@staticmethod
	def _to_serializable(obj):
		if isinstance(obj, BaseModel):
			return obj.model_dump()
		if isinstance(obj, dict):
			return {k: DapiException._to_serializable(v) for k, v in obj.items()}
		if isinstance(obj, list):
			return [DapiException._to_serializable(v) for v in obj]
		return obj

	def to_dict(self):
		return self._data

	def to_response(self):
		return JSONResponse(
			status_code = self.status_code,
			content     = self._data
		)

	@staticmethod
	def consume(e: Exception) -> 'DapiException':
		if isinstance(e, DapiException):
			# Дополняем контекст, если его нет
			context = e.context or {}

			if 'file' not in context or 'line' not in context:
				tb_lines = traceback.extract_tb(e.__traceback__)
				if tb_lines:
					context.setdefault('file', tb_lines[-1].filename)
					context.setdefault('line', tb_lines[-1].lineno)

			return DapiException(
				status_code = e.status_code,
				detail      = e.detail,
				severity    = e.severity,
				headers     = e.headers,
				context     = context
			)

		# Генерация новой ошибки, если это не DapiException
		error_type = e.__class__.__name__
		message    = str(e).strip()
		tb_lines   = traceback.extract_tb(e.__traceback__)
		filename   = tb_lines[-1].filename if tb_lines else '?'
		lineno     = tb_lines[-1].lineno   if tb_lines else '?'
		operator   = getattr(e, 'operator', None)

		if not operator:
			for frame in reversed(tb_lines):
				if 'operators' in frame.filename:
					operator = Path(frame.filename).stem
					break

		traceback.print_exception(type(e), e, e.__traceback__, limit=5)

		return DapiException(
			status_code = 500,
			severity    = DapiException.HALT,
			detail      = f'{error_type}: {message}',
			context     = {
				'error_type': error_type,
				'file'      : filename,
				'line'      : lineno,
				'operator'  : operator
			}
		)
