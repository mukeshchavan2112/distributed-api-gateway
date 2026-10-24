
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configuration: available backend instances.
BACKEND_URLS = [
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
]

# How long the gateway waits for the backend (seconds).
BACKEND_TIMEOUT_SECONDS = 5.0

# Headers that must not be forwarded between proxy connections.
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

# Headers set by the HTTP client for the new request.
HEADERS_SET_BY_CLIENT = {"host", "content-length"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create one shared HTTPX client and close it on shutdown."""
    app.state.http_client = httpx.AsyncClient(
        timeout=BACKEND_TIMEOUT_SECONDS
    )
    app.state.next_backend_index = 0

    yield

    await app.state.http_client.aclose()


app = FastAPI(title="API Gateway", lifespan=lifespan)


def filter_headers(headers: httpx.Headers | dict) -> dict:
    """Remove hop-by-hop and client-managed headers."""
    connection_value = headers.get("connection", "")
    named_in_connection = {
        name.strip().lower()
        for name in connection_value.split(",")
        if name.strip()
    }

    blocked = (
        HOP_BY_HOP_HEADERS
        | HEADERS_SET_BY_CLIENT
        | named_in_connection
    )

    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in blocked
    }


def error_response(status_code: int, message: str) -> JSONResponse:
    """Return a controlled error without internal details."""
    return JSONResponse(
        status_code=status_code,
        content={"error": message},
    )


@app.get("/health")
async def health():
    """Indicate that the gateway process is running."""
    return {"status": "ok", "service": "gateway"}


@app.get("/api/hello")
async def api_hello(request: Request):
    """Select a backend using round-robin and forward the request."""
    client: httpx.AsyncClient = request.app.state.http_client

    # Select the next backend and advance the counter.
    index = request.app.state.next_backend_index
    request.app.state.next_backend_index = (
        index + 1
    ) % len(BACKEND_URLS)

    backend_url = f"{BACKEND_URLS[index]}/hello"
    forward_headers = filter_headers(request.headers)

    try:
        upstream = await client.get(
            backend_url,
            headers=forward_headers,
        )
    except httpx.ConnectError:
        return error_response(
            503, "Backend service is unavailable."
        )
    except httpx.TimeoutException:
        return error_response(
            504, "Backend service timed out."
        )
    except httpx.RequestError:
        return error_response(
            502, "Gateway could not complete the backend request."
        )

    try:
        upstream_json = upstream.json()
    except ValueError:
        return error_response(
            502, "Backend returned a response that is not valid JSON."
        )

    return JSONResponse(
        status_code=upstream.status_code,
        content=upstream_json,
    )
