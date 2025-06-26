import os
from time import time

from typing          import Optional
from wordwield.lib.o import O
from wordwield       import ww


class GulpSchema(O):
	timestamp : int           = O.Field(description='Time of occurrence', llm=False, semantic=True)
	value     : str           = O.Field(description='Output value',       llm=True,  semantic=True)
	author    : Optional[str] = O.Field(description='Optional author',    llm=False, default=None)

	def __str__(self)  : return f'Gulp [{self.timestamp}] "{self.value}"'
	def __repr__(self) : return str(self)
	
	@classmethod
	def on_create(cls, data):
		data['timestamp'] = int(time())
		return data

class StreamSchema(O):
	name   : str                        = O.Field(semantic=True, description='Stream name', llm=False)
	role   : str                        = O.Field(description='Stream role', llm=False)
	gulps  : Optional[list[GulpSchema]] = O.Field(semantic=True, description='Ordered sequence of output values', default_factory=list, llm=False)
	author : Optional[str]              = O.Field(description='Name of agent who owns this stream')

	@classmethod
	def zip(cls, names):
		names = [names] if isinstance(names, str) else names
		gulps = []
		for name in names:
			stream = cls.load(name)
			for g in stream.gulps:
				g.author = stream.author
				gulps.append(g)
		gulps.sort(key=lambda g: g.timestamp)
		return cls(name='+'.join(names), gulps=gulps, author='', role='')
	
	@classmethod
	def zip_write(cls, names, texts):
		if isinstance(names, str) : names = [names]
		for name in names:
			stream = cls.load(name)
			if stream is None:
				stream = cls(name=name)
			stream.write(texts)
			stream.save()
		return cls

	def read(self, limit=None, since=None):
		gulps = self.gulps
		if since is not None:
			gulps = [g for g in self.gulps if g.timestamp > since]
		if limit is not None:
			limit = int(limit)
			gulps = gulps[-limit:] if limit > 0 else gulps
		for g in gulps:
			g.author = self.author or g.author
		return gulps

	def write(self, values):
		if isinstance(values, str): values = [values]
		for value in values:
			gulp = GulpSchema(value=str(value))
			self.gulps.append(gulp)
			self.log(value)
		return self
	
	def log(self, s):
		log_path = os.path.join(ww.config.LOGS_DIR, f'{self.name}.log')
		with open(log_path, 'a') as f:
			f.write(f'{s}\n')
	
	def to_list(self):
		return [g.value for g in self.gulps]