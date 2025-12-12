import os
from pathlib import Path
import glob

root = Path(__file__).resolve().parent / 'datasets'
output = Path(__file__).resolve().parent / 'en_ru.sentences.txt'

all_sents = []

# collect all .txt files under datasets/ (recursive)
for path in root.rglob('*.txt'):
	print('Reading:', path)
	with open(path, 'r', encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if len(line) > 0:
				all_sents.append(line)

print(f'Total sentences collected: {len(all_sents)}')

# shuffle for good training mix
import random
random.shuffle(all_sents)

# write to file (newline-separated)
with open(output, 'w', encoding='utf-8') as f:
	for s in all_sents:
		f.write(s + '\n')

print(f'Mixed dataset saved to: {output}')
