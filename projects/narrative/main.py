import sys, os, asyncio

LOG_DIR       = 'logs' 
EXPERTISE_DIR = 'expertise'
PROJECT_PATH  = os.path.abspath(os.path.dirname(__file__))
PROJECT_NAME  = os.path.basename(PROJECT_PATH)

ROOT = os.path.join(PROJECT_PATH, '..', '..')
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from wordwield import ww

################################################################

def main():
	ww.init(
		PROJECT_NAME=PROJECT_NAME,
		PROJECT_PATH=PROJECT_PATH,
	)
	# Now run the async call in the event loop
	asyncio.run(ww.operators.Test()())

if __name__ == "__main__":
	main()