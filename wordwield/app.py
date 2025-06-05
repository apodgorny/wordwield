import os

os.environ['PROJECT_PATH'] = os.path.dirname(
	os.path.dirname(
		os.path.abspath(__file__)
	)
)

# db_path = os.path.join(os.environ['PROJECT_PATH'], 'dapi.db')
# if os.path.exists(db_path):
# 	os.remove(db_path)

from fastapi                 import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from wordwield.controller import dapi
from wordwield.lib               import DapiException


app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins     = ['*'], # or ['http://127.0.0.1:8000']
	allow_methods     = ['*'],
	allow_headers     = ['*'],
	allow_credentials = True,
)
dapi.start(app)

@app.on_event('startup')
async def startup_event():
	await dapi.initialize_services()

@app.exception_handler(DapiException)
async def dapi_exception_handler(request: Request, exc: DapiException):
	return exc.to_response()

__all__ = ["app"]
