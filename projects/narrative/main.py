import sys, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from wordwield import ww

print('here')

from schemas.schemas import (
	BeatSchema,
	TimelineSchema,
	ThreadSchema,
	VoiceSchema
)
from operators import (
	Pipeline,
	Test
)
print('and here')
################################################################

ww.init(
	PROJECT_NAME  = 'Narrative',
	PROJECT_PATH  = os.path.abspath(os.path.dirname(__file__)),
	LOG_DIR       = 'logs',
	EXPERTISE_DIR = 'expertise'
)

ww.verbose = True
result = ww.invoke(Pipeline, name='pipeline')