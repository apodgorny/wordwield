import os
from time import time

from typing          import Optional
from wordwield.lib.o import O
from wordwield       import ww


class GulpSchema(O):
	timestamp : int           = O.Field(description='Time of occurrence', llm=False, semantic=True)
	value     : str           = O.Field(description='Output value',       llm=True,  semantic=True)
	author    : Optional[str] = O.Field(description='Optional author',    llm=False, default=None)

	def __str__(self)  : return f'Gulp [{self.timestamp}] {self.author}: "{self.value}"'
	def __repr__(self) : return str(self)
	
	@classmethod
	def on_create(cls, data):
		data['timestamp'] = int(time())
		return data
	
	def to_prompt(self):
		return f'{self.author}: "{self.value}"'

class StreamSchema(O):
	name   : str                              = O.Field(semantic=True, description='Stream name', llm=False)
	role   : str                              = O.Field(description='Stream role', llm=False)
	gulps  : Optional[list[GulpSchema]]       = O.Field(semantic=True, description='Ordered sequence of output values', default_factory=list, llm=False)
	author : Optional[str | list[str]]        = O.Field(description='Name(s) of agent(s) who owns this stream')

	# Private
	############################################################################################

	def _gulps_to_stream(self, gulps, author=None):
		'''Internal: return new StreamSchema with same meta but different gulps'''
		return StreamSchema(
			name   = self.name,
			role   = self.role,
			gulps  = gulps,
			author = author if author is not None else self.author
		)
	
	# Public
	############################################################################################

	@classmethod
	def zip(cls, *names):
		gulps   = []
		authors = set()

		for name in names:
			if stream := cls.load(name):
				if isinstance(stream.author, list):
					authors.update(stream.author)
				elif stream.author:
					authors.add(stream.author)
				for g in stream.gulps or []:
					g_copy = g.clone()
					g_copy.author = g_copy.author or stream.author
					gulps.append(g_copy)
		gulps.sort(key=lambda g: g.timestamp)
		authors = list(authors)

		return cls(
			name   = '+'.join(names),
			gulps  = gulps,
			author = authors if authors else None,
			role   = ''
		)

	def since(self, timestamp: int) -> "StreamSchema":
		return self._gulps_to_stream([g for g in self.gulps if g.timestamp > timestamp])

	def last(self, n: int) -> "StreamSchema":
		return self._gulps_to_stream(self.gulps[-n:] if n > 0 else [])

	def write(self, values, author=None):
		if isinstance(values, str) : values = [values]
		if author is None          : author = self.author or []
		if isinstance(author, str) : author = [author]

		authors = author if author else [self.name]
		for a in authors:
			stream = self.__class__.load(a)
			if stream is None:
				stream = self.__class__(name=a, author=a)
			stream.gulps = stream.gulps if isinstance(stream.gulps, list) else []
			for value in values:
				if not isinstance(value, str):
					raise ValueError(f'🛑 Cannot write non–string to stream `{stream.name}`')
				gulp = GulpSchema(value=str(value), author=a if author else None)
				stream.gulps.append(gulp)
				stream.save()
				stream.log(value)
		return self

	def read(self, limit=None, since=None):
		stream = self
		if since is not None:
			stream = stream.since(since)
		if limit is not None:
			stream = stream.last(int(limit))
		for g in stream.gulps:
			g.author = g.author or stream.author
		return stream.gulps

	def log(self, s):
		log_path = os.path.join(ww.config.LOGS_DIR, f'{self.name}.log')
		with open(log_path, 'a') as f:
			f.write(f'{s.strip()}\n')

	def to_list(self):
		return [g.value for g in self.gulps]

	def to_prompt(self):
		return '\n'.join([g.to_prompt() for g in self.gulps])
