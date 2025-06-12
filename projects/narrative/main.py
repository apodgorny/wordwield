import sys, os

LOG_DIR       = 'logs'
EXPERTISE_DIR = 'expertise'
PROJECT_PATH  = os.path.abspath(os.path.dirname(__file__))
PROJECT_NAME  = os.path.basename(PROJECT_PATH)

ROOT = os.path.join(PROJECT_PATH, '..', '..')
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from wordwield import ww

from operators import (
	Timeline
)

################################################################

ww.init(
	PROJECT_NAME  = PROJECT_NAME,
	PROJECT_PATH  = PROJECT_PATH,
	LOG_DIR       = LOG_DIR,
	EXPERTISE_DIR = EXPERTISE_DIR
)

ww.verbose = True
result = ww.invoke(Timeline, name=PROJECT_NAME, number=42)