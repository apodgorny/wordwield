import sys, os

PROJECT_PATH  = os.path.abspath(os.path.dirname(__file__))
PROJECT_NAME  = os.path.basename(PROJECT_PATH)

ROOT = os.path.join(PROJECT_PATH, '..', '..')
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from wordwield import ww

################################################################

ww.init(
	PROJECT_NAME=PROJECT_NAME,
	PROJECT_PATH=PROJECT_PATH,
)
ww(ww.operators.Narrative('fly')())
