import os.path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Stats import stats
from Classification import classification


out_file_path = os.path.abspath(os.path.curdir)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "127.0.0.1"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(stats)
app.include_router(classification)
app.include_router(auth, prefix="/auth")


