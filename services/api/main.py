from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes.health import router as health_router
from .routes.upload import router as upload_router
from .routes.parse import router as parse_router
from .routes.index import router as index_router
from .routes.ask import router as ask_router

app = FastAPI(title="Commerce GPT5 API", version="0.1.0")

# Minimal CORS; tighten later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(upload_router, prefix="/data", tags=["data"])
app.include_router(parse_router, prefix="/data", tags=["data"])
app.include_router(index_router, prefix="/data", tags=["data"])
app.include_router(ask_router, tags=["ask"]) 

# Serve the web app statically at /web
app.mount("/web", StaticFiles(directory="web", html=True), name="web")
