"""FastAPI entry point for PromptProxy Lite."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.proxy import router as proxy_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("prompt_proxy_lite")


app = FastAPI(
    title="PromptProxy Lite",
    description="Minimal OpenAI-compatible prompt-injecting proxy.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "PromptProxy Lite",
        "docs": "/docs",
        "health": "/health",
        "pro": "https://github.com/tlyyxjz/prompt-proxy-pro",
    }
