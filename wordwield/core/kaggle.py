# ==========================================================================================
# Utility assumes that you have ~/.kaggle/kaggle.json in your system
# kaggle.json is automatically downloaded when you go to kaggle website
# And generate "Legacy API Key" by clicking a button in settings
# Then do `mkdir ~/.kaggle` and `mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json`
# ==========================================================================================

import os
import time
import json
import zipfile
import tempfile

import torch
import requests

from tqdm import tqdm


class Kaggle:
	def __init__(self):
		self.kaggle_path      = os.path.expanduser('~/.kaggle')
		self.kaggle_json_path = os.path.join(self.kaggle_path, 'kaggle.json')
		self.datasets_path    = os.path.join(self.kaggle_path, 'datasets')
		self.timeout          = 60

		os.makedirs(self.kaggle_path,   exist_ok=True)
		os.makedirs(self.datasets_path, exist_ok=True)

		self.username, self.key = self._get_credentials()

	# ==========================================================================================
	# PRIVATE METHODS
	# ==========================================================================================

	# Check if file in question exists, if so, return it's path, else None
	# ------------------------------------------------------------------------------------------
	def _has_file(self, dataset_path, dataset_file):
		file_path = os.path.join(dataset_path, dataset_file)
		return file_path if os.path.isfile(file_path) else None

	# Try to find file and torch it
	# ------------------------------------------------------------------------------------------
	def _get_torch_file(self, dataset_id, dataset_path, dataset_file, device):
		file_path = self._has_file(dataset_path, dataset_file)
		if not file_path:
			raise RuntimeError(f'File `{dataset_file}` not found in dataset `{dataset_id}`')
		return torch.load(file_path, map_location=device)

	# Build download url
	# ------------------------------------------------------------------------------------------
	def _get_download_url(self, dataset_id):
		return f'https://www.kaggle.com/api/v1/datasets/download/{dataset_id}'

	# Read kaggle credentials
	# ------------------------------------------------------------------------------------------
	def _get_credentials(self):
		try:
			with open(self.kaggle_json_path, 'r') as f:
				token = json.load(f)

			username = token.get('username')
			key      = token.get('key')
		except Exception as e:
			raise ValueError(f'Warning: failed to read Kaggle token: {e}. \n(See instructions in kaggle.py)')

		if username and key:
			return username, key
		
		raise ValueError('Warning: Kaggle token missing username or key. \n(See instructions in kaggle.py)')

	# Get cache path for dataset
	# ------------------------------------------------------------------------------------------
	def _dataset_path(self, dataset_id):
		owner, dataset_name = dataset_id.split('/')
		return os.path.join(self.datasets_path, owner, dataset_name)
	
	# Download via Kaggle API
	# ------------------------------------------------------------------------------------------
	def _download(self, dataset_id, zip_path):
		auth     = (self.username, self.key)
		url      = self._get_download_url(dataset_id)

		print(f'Downloading dataset: {dataset_id}')
		try:
			with requests.get(
				url,
				auth    = auth,
				stream  = True,
				timeout = self.timeout
			) as response:
				if response.status_code == 200:
					total = int(response.headers.get('Content-Length', 0))
					chunk = 1024 * 1024
					with open(zip_path, 'wb') as f, tqdm(
						total      = total if total > 0 else None,
						unit       = 'B',
						unit_scale = True,
						desc       = f'Downloading `{dataset_id}`'
					) as bar:
						for data in response.iter_content(chunk_size=chunk):
							if data:
								f.write(data)
								bar.update(len(data))
				else:
					print(f'Warning: Kaggle download failed for {dataset_id}: HTTP {response.status_code}')
					return False
				
		except Exception as e:
			print(f'Warning: Kaggle download failed for {dataset_id}: {e}')
			return False
		
		return True

	# Extract downloaded file
	# ------------------------------------------------------------------------------------------
	def _extract(self, zip_path, target_dir):
		try:
			with zipfile.ZipFile(zip_path, 'r') as z:
				z.extractall(target_dir)
			print(f'Files have been extracted to `{target_dir}`')
			return True
		except zipfile.BadZipFile:
			print(f'Error: `{zip_path}` is a bad zip file or not a zip file.')
		except FileNotFoundError:
			print(f'Error: The file `{zip_path}` was not found.')
		except Exception as e:
			print(f'An unexpected error occurred: `{e}`')
		return False

	# ==========================================================================================
	# PUBLIC METHODS
	# ==========================================================================================
	
	# Download and extract dataset
	# ------------------------------------------------------------------------------------------
	def load(self, dataset_id, dataset_file, device=None):
		device = torch.device('cpu') if device is None else torch.device(device)

		dataset_path = self._dataset_path(dataset_id)
		result       = None

		if self._has_file(dataset_path, dataset_file):
			result = self._get_torch_file(dataset_id, dataset_path, dataset_file, device)
		else:
			os.makedirs(dataset_path, exist_ok=True)
			with tempfile.TemporaryDirectory() as dirpath:
				zip_path = os.path.join(dirpath, dataset_id.replace('/','__') + '.zip')
				if self._download(dataset_id, zip_path):
					if self._extract(zip_path, dataset_path):
						result = self._get_torch_file(dataset_id, dataset_path, dataset_file, device)

		return result
