# Wolfram Language Server

A FastAPI-based backend server for executing Wolfram Language scripts using the `wolframclient` Python library.

## Features

- **Execute Wolfram Language Code**: Run arbitrary Wolfram Language scripts
- **Simple Expression Evaluation**: Quick evaluation of mathematical expressions
- **Security**: Code validation, rate limiting, and optional authentication
- **Async Support**: Non-blocking execution with proper timeout handling
- **Health Monitoring**: Built-in health checks and status endpoints
- **OpenAPI Documentation**: Auto-generated API documentation

## Requirements

- Python 3.13+
- Wolfram Engine or Mathematica installed
- `uv` package manager

## Installation

1. **Navigate to the directory:**
   ```bash
   cd wolfram-language-server
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (especially WOLFRAM_KERNEL_PATH)
   ```

## Usage

### Start the Server

```bash
# Using uv
uv run python -m wolfram_language_server.main
```

The server will start on `http://localhost:8000` by default.

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Execute Wolfram Language Code (Strict Syntax)
```bash
curl -X POST http://localhost:8000/execute-wolfram \
  -H "Content-Type: application/json" \
  -d '{
    "code": "Solve[x^2 + 2x - 3 == 0, x]",
    "timeout": 30
  }'
```

#### Query Wolfram Alpha (Natural Language)
```bash
curl -X POST http://localhost:8000/wolfram-alpha \
  -H "Content-Type: application/json" \
  -d '{
    "query": "solve x^2 + 2x - 3 = 0",
    "timeout": 30,
    "format": "Result"
  }'
```

## Security Features

### Code Validation
The server validates Wolfram Language code for potentially dangerous operations.

### Rate Limiting
- Default: 30 requests per minute per IP
- Burst limit: 5 requests

### Authentication
Optional Bearer token authentication via `API_KEY` environment variable.

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.