import sys, os

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_NAME = os.path.basename(PROJECT_PATH)

ROOT = os.path.join(PROJECT_PATH, '..', '..')
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from wordwield import ww

################################################################

# Initialize WordWield
ww.init(
	PROJECT_NAME = PROJECT_NAME,
	PROJECT_PATH = PROJECT_PATH,
	reset_db     = True
)

ww.schemas.StorySchema.put(
	name  = PROJECT_NAME,
	title = 'Пыль',
	genre = 'секс драма'
)

# ww(ww.operators.Narrative(PROJECT_NAME)())
ww(ww.operators.Main(PROJECT_NAME)(
	foo  = 'Bar'
))

# ww(ww.operators.Characters(PROJECT_NAME)())
