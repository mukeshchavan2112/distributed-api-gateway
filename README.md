# Lightweight API Gateway

A Python-based API gateway that forwards requests to multiple backend instances using round-robin load balancing. It includes basic backend fault handling and automated tests.

## Features

- **Round-robin load balancing:** Distributes incoming requests across two configured backend instances.
- **Request forwarding:** Routes requests from the gateway to a backend service.
- **Timeout handling:** Returns an HTTP `504 Gateway Timeout` when a backend request times out.
- **Connection failure handling:** Returns an HTTP `503 Service Unavailable` when a backend cannot be reached.
- **Invalid JSON handling:** Returns an HTTP `502 Bad Gateway` when a backend response cannot be parsed as JSON.
- **Health endpoint:** Provides a simple endpoint to check whether the gateway process is running.
- **Automated tests:** Uses pytest and FastAPI's test client to verify core routing and error-handling behavior.

## Technology Stack

- Python
- FastAPI
- Uvicorn
- HTTPX
- pytest
- Locust (for load testing and performance measurement)

## Project Structure

```text
lightweight-api-gateway/
├── app/
│   ├── __init__.py
│   └── main.py                 # API gateway and request routing
├── services/
│   ├── __init__.py
│   ├── backend.py              # Backend A service
│   └── backend_b.py            # Backend B service
├── tests/
│   └── test_gateway.py         # Automated gateway tests
├── .gitignore                  # Files excluded from Git
├── locustfile.py               # Locust load-testing scenarios
├── README.md                   # Project documentation
└── requirements.txt            # Python dependencies
```

### Key Components

- **`app/main.py`** — Implements the API gateway, round-robin backend selection, request forwarding, and upstream error handling.
- **`services/backend.py`** — Implements the first backend service.
- **`services/backend_b.py`** — Implements the second backend service.
- **`tests/test_gateway.py`** — Tests gateway routing and error-handling behavior.
- **`locustfile.py`** — Defines simulated client requests for load testing with Locust.
- **`requirements.txt`** — Lists the Python packages required to run and test the project.

## Architecture

The gateway listens on port `8000` and forwards requests to two backend instances:

| Component | Address | Purpose |
|---|---|---|
| API Gateway | `http://127.0.0.1:8000` | Routes client requests |
| Backend A | `http://127.0.0.1:8001` | First backend instance |
| Backend B | `http://127.0.0.1:8002` | Second backend instance |

For requests to `/api/hello`, the gateway selects the next backend in round-robin order and forwards the request to that backend's `/hello` endpoint.

## Prerequisites

- Python 3.10 or later
- pip
- Git (optional, for cloning the repository)

## Setup

Clone the repository:

```bash
git clone https://github.com/mukeshchavan2112/distributed-api-gateway.git
cd distributed-api-gateway
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Project

Start each service in a separate terminal from the project root, activating the virtual environment in each terminal.

**Terminal 1 — Backend A**

```powershell
python -m uvicorn services.backend:app --host 127.0.0.1 --port 8001
```

**Terminal 2 — Backend B**

```powershell
python -m uvicorn services.backend_b:app --host 127.0.0.1 --port 8002
```

**Terminal 3 — API Gateway**

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks whether the gateway process is running |
| GET | `/api/hello` | Forwards a request to the selected backend |

### Example Request

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/hello
```

Example response from Backend A:

```json
{
  "backend": "backend-a",
  "message": "Hello from backend-a"
}
```

The `backend` field identifies which backend handled the request.

### Verify Round-Robin Routing

```powershell
1..6 | ForEach-Object {
    $response = Invoke-RestMethod http://127.0.0.1:8000/api/hello
    Write-Output "Request $_ : $($response.backend)"
}
```

With both backends running and no other requests affecting the counter, consecutive requests should alternate between Backend A and Backend B.

## Error Handling

The gateway maps common upstream failures to controlled HTTP responses:

| Scenario | Gateway response |
|---|---|
| Backend connection failure | `503 Service Unavailable` |
| Backend request timeout | `504 Gateway Timeout` |
| Other HTTPX request error | `502 Bad Gateway` |
| Invalid JSON from backend | `502 Bad Gateway` |

## Running Automated Tests

Run the tests from the project root:

```bash
python -m pytest -v
```

The current test suite covers:

- Gateway health check
- Round-robin load balancing
- Backend connection failure
- Backend timeout
- Invalid backend JSON

## Performance Testing

The gateway was tested locally using Locust.

### Test Configuration

| Parameter | Value |
|---|---|
| Simulated users | 10 |
| User spawn rate | 3 users/second |
| Test duration | 1 minute |
| Target endpoint | `GET /api/hello` |
| Environment | Local Windows development machine |

### Results

| Metric | Result |
|---|---:|
| Total requests | 596 |
| Failed requests | 0 |
| Average response time | 13.95 ms |
| Median response time | 14 ms |
| 95th percentile response time | 21 ms |
| 99th percentile response time | 28 ms |
| Maximum response time | 36 ms |
| Displayed request rate | 6.5 requests/second |

### Interpretation and Limitations

In this test run, Locust reported no failed requests. The measured average response time was 13.95 ms, and the 95th percentile was 21 ms.

These results describe one local test run and are not a production capacity guarantee. Results may vary with hardware, background activity, concurrency, and test conditions. A direct-backend comparison and repeated runs would be needed for a stronger performance evaluation.

## Current Limitations

- Backend instances are configured directly in the application.
- Only the `/api/hello` route is currently proxied.
- Round-robin selection is basic and does not assess backend health before routing.
- The health endpoint reports gateway process status; it does not verify the health of every backend.
- Automated failure tests use mocked backend responses.
- Production-scale capacity and high-concurrency performance have not yet been established.

## Future Improvements

Potential future work includes:

- Configurable backend instances
- More comprehensive integration tests
- Repeated benchmarks under different concurrency levels
- Comparison with direct backend requests
- More comprehensive integration tests
- Configurable backend instances
- Improved backend health monitoring and routing behavior
- Improved backend health monitoring and routing behavior
