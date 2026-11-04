import json
import logging
import sys
import time
import uuid
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.config import settings

logger = logging.getLogger("moodwave.access")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class RateLimiter:
    def __init__(self, limit_per_minute: int = 60):
        self.limit_per_minute = limit_per_minute
        self.requests: Dict[str, List[float]] = {}

    def is_rate_limited(self, ip: str, now: float) -> tuple[bool, int]:
        limit = settings.RATE_LIMIT_PER_MINUTE
        window = 60.0
        cutoff = now - window

        if ip not in self.requests:
            self.requests[ip] = []

        # Keep timestamps within the 60-second window
        valid_timestamps = [ts for ts in self.requests[ip] if ts > cutoff]
        self.requests[ip] = valid_timestamps

        if len(valid_timestamps) >= limit:
            oldest = valid_timestamps[0]
            retry_after = max(1, int(window - (now - oldest)))
            return True, retry_after

        self.requests[ip].append(now)
        return False, 0

    def reset(self):
        self.requests.clear()

rate_limiter = RateLimiter()

class MoodwaveMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Request ID handling
        incoming_request_id = request.headers.get("X-Request-ID")
        request_id = incoming_request_id if incoming_request_id else uuid.uuid4().hex
        request.state.request_id = request_id

        # Client IP extraction
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif request.client and request.client.host:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        now = time.time()
        start_time = time.perf_counter()

        # Check rate limit (exclude health check if desired, but applying uniformly works)
        is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, now)
        if is_limited:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_payload = {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Try again later.",
                    "request_id": request_id,
                }
            }
            log_entry = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": 429,
                "duration_ms": duration_ms,
            }
            logger.info(json.dumps(log_entry))
            response = JSONResponse(
                status_code=429,
                content=error_payload,
                headers={"Retry-After": str(retry_after), "X-Request-ID": request_id},
            )
            return response

        try:
            response = await call_next(request)
        except Exception:
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # Log request as one JSON line without query text or body
        log_entry = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }
        if hasattr(request.state, "query_length"):
            log_entry["query_length"] = request.state.query_length
        elif request.url.query:
            log_entry["query_length"] = len(request.url.query)

        logger.info(json.dumps(log_entry))
        return response
