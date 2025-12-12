#==================================================
# Test: Encoder → AP → Decoder nearest words
#==================================================
import os
import sys

os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Add repo root so `import wordwield` works when running as a script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from wordwield.lib.encoder      import Encoder
from wordwield.lib.word_decoder import WordDecoder


#==================================================
# Main test
#==================================================

def test():
	# --------------------------------------------------
	# Load Encoder
	# --------------------------------------------------
	encoder = Encoder()

	# If encoder loads trained weights normally — call it here:
	# encoder.load('trained/encoder.pt')

	# --------------------------------------------------
	# Encode a sentence to AP
	# --------------------------------------------------
	text = 'Александр печет вкусный хлебушек'
	ap = encoder.encode(text)

	# --------------------------------------------------
	# Load Decoder vocabulary
	# --------------------------------------------------
	dec = WordDecoder()
	if not dec.load():
		print(f'Failed to load decoder vocabulary from kaggle')
		return None

	print(f'\nLoaded vocabulary: {len(dec.words)} words')

	# --------------------------------------------------
	# Decode AP → nearest words
	# --------------------------------------------------
	results = dec.decode(ap, top_k=20)

	print('\nNearest words:')
	for w, s in results:
		print(f'{s:.4f}  {w}')

	return None

#==================================================
# Entrypoint
#==================================================

if __name__ == '__main__':
	test()
