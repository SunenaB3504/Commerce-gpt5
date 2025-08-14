from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils.middleware import ContentLengthLimitMiddleware, RequestTimeoutMiddleware
from fastapi.staticfiles import StaticFiles

from .routes.health import router as health_router
from .routes.upload import router as upload_router
from .routes.parse import router as parse_router
from .routes.index import router as index_router
from .routes.ask import router as ask_router
from .routes.validate import router as validate_router
from .routes.teach import router as teach_router
from .routes.mcq import router as mcq_router
from .routes.practice import router as practice_router
from .routes.eval import router as eval_router
from .routes.admin import router as admin_router

app = FastAPI(title="Commerce GPT5 API", version="0.1.0")

# Minimal CORS; tighten later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global middlewares for Day 8 hardening
app.add_middleware(ContentLengthLimitMiddleware)
app.add_middleware(RequestTimeoutMiddleware)

app.include_router(health_router)
app.include_router(upload_router, prefix="/data", tags=["data"])
app.include_router(parse_router, prefix="/data", tags=["data"])
app.include_router(index_router, prefix="/data", tags=["data"])
app.include_router(ask_router, tags=["ask"]) 
app.include_router(validate_router, tags=["validate"])
app.include_router(teach_router, tags=["teach"]) 
app.include_router(mcq_router, tags=["mcq"]) 
app.include_router(practice_router, tags=["practice"]) 
app.include_router(eval_router, tags=["eval"]) 
app.include_router(admin_router)

# Serve the web app statically at /web
app.mount("/web", StaticFiles(directory="web", html=True), name="web")
