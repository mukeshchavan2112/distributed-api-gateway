# Lightweight API Gateway with Load Balancing and Fault Handling

A small Python learning project. **Milestone 1** has two FastAPI apps:

- **Backend** (`services/backend.py`) on port 8001
- **Gateway** (`app/main.py`) on port 8000, which forwards requests to the backend

Load balancing and fault handling beyond a basic error response are planned for later milestones.

## Project structure

```text
Distributed_API_Gateway/
├── app/
│   ├── __init__.py
│   └── main.py          # gateway
├── services/
│   ├── __init__.py
│   └── backend.py       # backend-a
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

Run these in PowerShell from the project folder:

```powershell
cd D:\Distributed_API_Gateway
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activation script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Run

Use two separate PowerShell terminals. Activate `.venv` in both.

**Terminal 1: backend (port 8001)**

```powershell
cd D:\Distributed_API_Gateway
.\.venv\Scripts\Activate.ps1
uvicorn services.backend:app --host 127.0.0.1 --port 8001
```

**Terminal 2: gateway (port 8000)**

```powershell
cd D:\Distributed_API_Gateway
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Test

Open a third PowerShell terminal.

Backend directly:

```powershell
curl.exe http://127.0.0.1:8001/hello
```

Gateway health (does not check the backend):

```powershell
curl.exe http://127.0.0.1:8000/health
```

Gateway forwarding to the backend:

```powershell
curl.exe http://127.0.0.1:8000/api/hello
```

Test the failure case: stop the backend with `Ctrl+C`, then run:

```powershell
curl.exe -i http://127.0.0.1:8000/api/hello
```

Expected: HTTP `503` with a JSON error message.