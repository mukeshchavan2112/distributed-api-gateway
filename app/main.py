from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configuration: where the backend service lives.
BACKEND_BASE_URL = "http://127.0.0.1:8001"
BACKEND_HELLO_URL = f"{BACKEND_BASE_URL}/hello"

# How long the gateway waits for the backend before giving up (seconds).
BACKEND_TIMEOUT_SECONDS = 5.0

# Hop-by-hop headers only make sense for a single connection between two
# neighbours. A proxy must not pass them along to the next hop.
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

# Headers the HTTP client should set itself for the new request.
HEADERS_SET_BY_CLIENT = {"host", "content-length"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create one shared HTTPX client on startup and close it on shutdown."""
    app.state.http_client = httpx.AsyncClient(timeout=BACKEND_TIMEOUT_SECONDS)
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="API Gateway", lifespan=lifespan)


def filter_headers(headers: httpx.Headers | dict) -> dict:
    """Return a copy of the headers without hop-by-hop headers.

    Headers named inside the 'Connection' header are also hop-by-hop,
    so they are removed too.
    """
    connection_value = headers.get("connection", "")
    named_in_connection = {
        name.strip().lower() for name in connection_value.split(",") if name.strip()
    }

    blocked = HOP_BY_HOP_HEADERS | HEADERS_SET_BY_CLIENT | named_in_connection
    return {k: v for k, v in headers.items() if k.lower() not in blocked}


def error_response(status_code: int, message: str) -> JSONResponse:
    """Build a controlled error response (no traceback, no internal details)."""
    return JSONResponse(status_code=status_code, content={"error": message})


@app.get("/health")
async def health():
    """Only reports that the gateway process is running, not the backend."""
    return {"status": "ok", "service": "gateway"}


@app.get("/api/hello")
async def api_hello(request: Request):
    """Forward the request to the backend and return its status and JSON."""
    client: httpx.AsyncClient = request.app.state.http_client
    forward_headers = filter_headers(request.headers)

    try:
        upstream = await client.get(BACKEND_HELLO_URL, headers=forward_headers)
    except httpx.ConnectError:
        return error_response(503, "Backend service is unavailable.")
    except httpx.TimeoutException:
        return error_response(504, "Backend service timed out.")
    except httpx.RequestError:
        return error_response(502, "Gateway could not complete the backend request.")

    try:
        upstream_json = upstream.json()
    except ValueError:
        return error_response(502, "Backend returned a response that is not valid JSON.")

    return JSONResponse(
    status_code=upstream.status_code,
    content=upstream_json,
    )
