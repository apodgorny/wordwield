import traceback
from pathlib import Path
from pydantic import BaseModel

class WwException(Exception):
	HALT   = 'halt'
	BEWARE = 'beware'
	FYI    = 'fyi'

	def __init__(
		self,
		detail      = 'An error occurred',
		severity    = None,
		context     = None
	):
		self.detail   = detail
		self.severity = severity or self.HALT
		self.context  = context or {}

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
			return {k: WwException._to_serializable(v) for k, v in obj.items()}
		if isinstance(obj, list):
			return [WwException._to_serializable(v) for v in obj]
		return obj

	def to_dict(self):
		return self._data

	@staticmethod
	def consume(e: Exception) -> 'WwException':
		if isinstance(e, WwException):
			context = e.context or {}
			if 'file' not in context or 'line' not in context:
				tb_lines = traceback.extract_tb(e.__traceback__)
				if tb_lines:
					context.setdefault('file', tb_lines[-1].filename)
					context.setdefault('line', tb_lines[-1].lineno)
			return WwException(
				detail   = e.detail,
				severity = e.severity,
				context  = context
			)

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
		# Optionally print stacktrace for diagnostics
		traceback.print_exception(type(e), e, e.__traceback__, limit=5)
		return WwException(
			detail   = f'{error_type}: {message}',
			severity = WwException.HALT,
			context  = {
				'error_type': error_type,
				'file'      : filename,
				'line'      : lineno,
				'operator'  : operator
			}
		)
