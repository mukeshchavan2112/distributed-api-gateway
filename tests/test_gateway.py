
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app, filter_headers


@pytest.fixture
def client():
    """Start the gateway and close its resources after each test."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_backend(client):
    """Replace the HTTP client for a test and restore it afterward."""
    original_client = app.state.http_client
    mock_client = None

    def install(handler):
        nonlocal mock_client

        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )
        app.state.http_client = mock_client

    yield install

    # Restore the original client before the application's shutdown.
    app.state.http_client = original_client

    if mock_client is not None:
        client.portal.call(mock_client.aclose)


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "gateway",
    }


def test_round_robin_load_balancing(client):
    responses = [
        client.get("/api/hello")
        for _ in range(4)
    ]

    assert all(response.status_code == 200 for response in responses)

    backends = [
        response.json()["backend"]
        for response in responses
    ]

    assert backends == [
        "backend-a",
        "backend-b",
        "backend-a",
        "backend-b",
    ]


def test_backend_connection_failure_returns_503(client, mock_backend):
    def raise_connection_error(request):
        raise httpx.ConnectError(
            "Connection failed",
            request=request,
        )

    mock_backend(raise_connection_error)

    response = client.get("/api/hello")

    assert response.status_code == 503
    assert response.json() == {
        "error": "Backend service is unavailable."
    }


def test_backend_timeout_returns_504(client, mock_backend):
    def raise_timeout(request):
        raise httpx.ReadTimeout(
            "Request timed out",
            request=request,
        )

    mock_backend(raise_timeout)

    response = client.get("/api/hello")

    assert response.status_code == 504
    assert response.json() == {
        "error": "Backend service timed out."
    }


def test_invalid_backend_json_returns_502(client, mock_backend):
    def return_invalid_json(request):
        return httpx.Response(
            200,
            text="this is not valid JSON",
        )

    mock_backend(return_invalid_json)

    response = client.get("/api/hello")

    assert response.status_code == 502
    assert response.json() == {
        "error": "Backend returned a response that is not valid JSON."
    }


def test_other_backend_request_error_returns_502(client, mock_backend):
    def raise_request_error(request):
        raise httpx.RequestError(
            "Unexpected upstream request failure",
            request=request,
        )

    mock_backend(raise_request_error)

    response = client.get("/api/hello")

    assert response.status_code == 502
    assert response.json() == {
        "error": "Gateway could not complete the backend request."
    }


def test_backend_error_status_and_json_are_preserved(client, mock_backend):
    def return_backend_error(request):
        return httpx.Response(
            418,
            json={"error": "Backend rejected the request"},
        )

    mock_backend(return_backend_error)

    response = client.get("/api/hello")

    assert response.status_code == 418
    assert response.json() == {
        "error": "Backend rejected the request"
    }


def test_filter_headers_removes_hop_by_hop_and_connection_named_headers():
    headers = httpx.Headers({
        "Connection": "keep-alive, X-Internal",
        "Keep-Alive": "timeout=5",
        "X-Internal": "do-not-forward",
        "Host": "client.example",
        "X-Request-ID": "request-123",
    })

    filtered = filter_headers(headers)

    assert "connection" not in filtered
    assert "keep-alive" not in filtered
    assert "x-internal" not in filtered
    assert "host" not in filtered
    assert {
        key.lower(): value
        for key, value in filtered.items()
    }["x-request-id"] == "request-123"