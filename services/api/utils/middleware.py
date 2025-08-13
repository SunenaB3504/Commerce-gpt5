from __future__ import annotations

import os
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def _get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


class ContentLengthLimitMiddleware(BaseHTTPMiddleware):
    """Rejects requests whose Content-Length exceeds MAX_UPLOAD_MB.

    Applied broadly but primarily affects /data/upload and /data/index with file uploads.
    """

    def __init__(self, app, max_mb: int | None = None) -> None:
        super().__init__(app)
        self.max_bytes = (max_mb or _get_int_env("MAX_UPLOAD_MB", 64)) * 1024 * 1024

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]):
        try:
            cl = request.headers.get("content-length")
            if cl is not None:
                if int(cl) > self.max_bytes:
                    from starlette.responses import PlainTextResponse
                    return PlainTextResponse("Payload too large", status_code=413)
        except Exception:
            # If header invalid, fall through and let route validate
            pass
        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Times out slow requests using asyncio.wait_for.

    Note: This cannot interrupt CPU-bound work; it only aborts the response with 504.
    """

    def __init__(self, app, seconds: int | None = None) -> None:
        super().__init__(app)
        self.seconds = seconds or _get_int_env("REQUEST_TIMEOUT_SEC", 180)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.seconds)
        except asyncio.TimeoutError:
            from starlette.responses import PlainTextResponse
            return PlainTextResponse("Request timeout", status_code=504)
