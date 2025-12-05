from .string    import String
from .highlight import Highlight

class Frame:
	def __init__(
		self,
		name       : str,
		lineno     : int   = 1,
		restrict   : bool  = True,
		file       : str   = None,
		line       : str   = None,
		importance : float = 0
	):
		self.name       = name
		self.file       = file
		self.line       = line
		self.lineno     = lineno
		self.restrict   = restrict
		self.importance = importance
		self.subframes  = []

class ExecutionContext:
	def __init__(self,
		enable_color  : bool  = True,
		enable_code   : bool  = True,
		importance    : float = 0.5
	):
		self._root        = Frame(name='root', lineno=0, restrict=True)
		self._stack       = [self._root]
		self._indent      = 0
		self._indent_text = String.color(' ', String.GRAY) if enable_color else ' '
		self.i            = ''

		self.enable_color  = enable_color
		self.enable_code   = enable_code
		self.enable_detail = True
		self.importance    = importance

	#################################################################

	def _get_code(self, frame):
		if self.enable_code and frame.line:
			code = frame.line.strip() + '\n'
			if self.enable_color:
				code = Highlight.python(code).replace('\n', '')
			return code
		return ''

	def _get_block_icon(self, frame):
		if not self.enable_color:
			return '▮'
		color = String.RED if frame.restrict else String.GREEN
		return String.color('▮', color)

	def _get_name(self, frame):
		return frame.name

	def _get_detail(self, detail=''):
		if self.enable_color:
			detail = String.color(detail, String.GRAY, 'i')
		return detail

	def _get_direction(self, is_push):
		direction = '→' if is_push else '←'
		if self.enable_color:
			color = String.GREEN if is_push else String.RED
			direction = String.color(direction, color)
		return direction

	def _get_line(self, frame, is_push=True, detail=None):
		icon      = self._get_block_icon(frame)
		name      = self._get_name(frame)
		code      = self._get_code(frame)
		detail    = self._get_detail(detail)
		direction = self._get_direction(is_push)
		left      = f'{icon}{self.i} {direction} {name} :'
		return    f'{left} {code}{detail}'

	#################################################################

	@property
	def current(self) -> Frame:
		return self._stack[-1]

	def _color(self, text: str) -> str:
		if self.enable_color:
			return String.color(text, String.LIGHTGRAY)
		return text

	def update_indent(self, n: int):
		self._indent += n
		self.i = self._color(self._indent_text) * self._indent

	def push(self, 
		name       : str,
		lineno     : int   = 1,
		restrict   : bool  = True,
		file       : str   = None,
		line       : str   = None,
		importance : float = 0,
		detail     : str   = None
	):
		frame = Frame(
			name       = name,
			file       = file,
			line       = line,
			lineno     = lineno,
			restrict   = restrict,
			importance = importance
		)

		self.current.subframes.append(frame)
		self._stack.append(frame)

		if frame.importance > self.importance:
			print(self._get_line(frame=frame, is_push=True, detail=detail))
		self.update_indent(1)

	def pop(self, detail=None):
		if len(self._stack) > 1:
			frame = self._stack.pop()
			if not self.enable_detail and frame.restrict:
				self.update_indent(-1)
				return
			
			self.update_indent(-1)
			if frame.importance > self.importance:
				print(self._get_line(frame, is_push=False, detail=detail))
