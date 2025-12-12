#==================================================
# Train vocabulary embeddings for Decoder
# Downloads RU + EN wordlists, merges them,
# embeds via Decoder, saves state
#==================================================

import os
import sys
import requests

# Add repo root so `import wordwield` works when running as a script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)


from wordwield.lib.decoder import Decoder


#==================================================
# Download helper
#==================================================

def download(url, path, min_freq=5):
	# --------------------------------------------------
	# Download + filter a frequency wordlist
	# --------------------------------------------------
	if os.path.exists(path):
		return path

	print(f'Downloading: {url}')
	resp = requests.get(url, timeout=60)
	resp.raise_for_status()

	lines = resp.text.splitlines()
	words = []

	for line in lines:
		parts = line.strip().split()
		if len(parts) < 2:
			continue

		word = parts[0]
		try:
			freq = int(parts[1])
		except:
			continue

		if freq >= min_freq:
			words.append(word)

	with open(path, 'w') as f:
		for w in words:
			f.write(w + '\n')

	print(f'Saved filtered wordlist ({len(words)} words): {path}')

	return path


#==================================================
# Build vocabulary embeddings and save
#==================================================

def train(output_pt='decoder_vocab.pt'):
	# --------------------------------------------------
	# Download RU + EN wordlists
	# --------------------------------------------------
	ru_url = 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ru/ru_full.txt'
	en_url = 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_full.txt'

	ru_txt = download(ru_url, 'ru_full.txt')
	en_txt = download(en_url, 'en_full.txt')

	with open(ru_txt, 'r') as f:
		ru_words = [w.strip() for w in f.readlines() if len(w.strip()) > 1]

	with open(en_txt, 'r') as f:
		en_words = [w.strip() for w in f.readlines() if len(w.strip()) > 1]

	words = ru_words + en_words
	print(f'Total words loaded: {len(words)}')

	# --------------------------------------------------
	# Embed + Save using Decoder
	# --------------------------------------------------
	dec = Decoder()
	dec.embed(words)
	dec.save(output_pt)

	print(f'Saved vocabulary embeddings to: {output_pt}')
	return output_pt


#==================================================
# Entrypoint
#==================================================

if __name__ == '__main__':
	train('/Users/alexander/dev/wordwield/wordwield/lib/weights/decoder.pt')
