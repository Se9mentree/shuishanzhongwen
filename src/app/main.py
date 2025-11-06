# file: app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .database import engine, Base
from .routers import all_routers



app = FastAPI(title="My App")


ALLOWED_ORIGINS = [
    "http://49.52.27.69:8789",  
    "http://localhost:8789",
    "http://127.0.0.1:8789",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  
    allow_credentials=True,
    allow_methods=["*"],            
    allow_headers=["*"],           
)


MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/data/media")
if os.path.isdir(MEDIA_ROOT):
    app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")
else:
    print(f"⚠️ MEDIA_ROOT 路径不存在: {MEDIA_ROOT}")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


for r in all_routers:
    app.include_router(r)



