import httpx, pytest


GATEWAY_URL = "http://127.0.0.1:8000"


@pytest.mark.integration
def test_gateway_forwards_request_to_real_backend():
    response = httpx.get(
        f"{GATEWAY_URL}/api/hello",
        timeout=3.0,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["backend"] in {"backend-a", "backend-b"}
    assert data["message"] in {
        "Hello from backend-a",
        "Hello from backend-b",
    }


@pytest.mark.integration
def test_gateway_round_robin_with_real_backends():
    observed_backends = []

    for _ in range(6):
        response = httpx.get(
            f"{GATEWAY_URL}/api/hello",
            timeout=3.0,
        )

        assert response.status_code == 200
        observed_backends.append(response.json()["backend"])

    assert set(observed_backends) == {"backend-a", "backend-b"}

    for index in range(1, len(observed_backends)):
        assert observed_backends[index] != observed_backends[index - 1]
