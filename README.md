# FastAPI Loki Observability Suite

**Production-ready Python/FastAPI Observability Stack**

This module provides end-to-end logging, tracing, and monitoring for Python microservices using:

- **Grafana Loki** (log aggregation, querying)
- **Grafana Alloy** (log shipping, enrichment)
- **OpenTelemetry Collector** (distributed tracing, metrics)
- **Grafana Tempo** (distributed tracing, trace storage, and search)
- **FastAPI** (microservice framework)
- **Docker Compose** (orchestration)
- **Pytest & Pydantic** (testing, type safety)

## 🚀 Features

- Secure, environment-variable-driven configuration (no hardcoded secrets)
- CI/CD optimized, ephemeral test environments
- Strict type validation with Pydantic
- End-to-end and integration tests for log ingestion and query
- TLS/HTTPS, multi-tenant, and admin API scenarios
- Ready for cloud, Kubernetes, or local Docker Compose
- **Tempo support:** Easily enable distributed tracing and trace search for FastAPI and Python apps

## 🧩 Tempo Support (Distributed Tracing)

**Grafana Tempo** enables full distributed tracing for your Python/FastAPI microservices:

- Collects traces from OpenTelemetry SDKs, FastAPI middleware, and instrumented libraries.
- Stores and indexes traces for search and correlation with logs (Loki) and metrics (Prometheus).
- Visualize traces and spans in Grafana dashboards for root cause analysis and performance monitoring.

**How to Enable Tempo:**

1. Uncomment the Tempo stage in the [Dockerfile](./docker/poetry/Dockerfile) and provide a production-ready `tempo-config.yaml`.
2. Expose ports 3200 (Tempo API) and 4317 (OTLP gRPC) as needed.
3. Ensure your FastAPI or Python app is instrumented with OpenTelemetry SDKs:
   ```python
   from opentelemetry import trace
   from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
   from fastapi import FastAPI
   app = FastAPI()
   FastAPIInstrumentor.instrument_app(app)
   # Configure exporters to point to your Tempo endpoint
   ```
4. Set the OTLP exporter endpoint to point to your running Tempo instance (e.g., `TEMPO_EXPORTER_ENDPOINT`).
5. View, search, and correlate traces in Grafana.

**Trace Use Cases:**

- End-to-end request tracing across microservices
- Root cause analysis for latency and errors
- Correlate logs, metrics, and traces for unified observability

## 🏷️ Tags

`python, fastapi, loki, tempo, observability, monitoring, tracing, opentelemetry, grafana, docker, pytest, pydantic`

## 📁 Folder Structure & Conventions

```
loki/
├── _docs/           # Markdown docs, best practices, diagrams, usage
├── _tests/          # Unit/integration tests for all core logic
├── config.py        # Singleton config (class-based, imports from global settings)
├── docker/          # Dockerfile, docker-compose, provisioning config, env
├── models/          # Pydantic models or log schemas
├── exceptions/      # Custom exceptions for observability
├── <core>.py        # Main implementation (health.py, log ingestion, etc.)
├── README.md        # Main readme (this file)
```

- **_docs/**: All documentation, diagrams, and best practices for this module.
- **_tests/**: All tests for this module, including ingestion, smoke, and integration tests.
- **config.py**: Singleton config pattern, imports from global settings, exposes all constants for this module.
- **docker/**: Containerization assets (Dockerfile, docker-compose, provisioning configs, .env.example, etc).
- **models/**: Pydantic models or log schemas for input/output validation.
- **exceptions/**: Custom exception classes for robust error handling.
- **<core>.py**: Main implementation modules (e.g., health.py, log ingestion, etc).

---

## 🏗️ Singleton & Config Pattern
- Use a single class (e.g., `LokiConfig`) in `config.py` to centralize all env, log, and integration settings.
- Import from global settings to avoid duplication and ensure DRY config.
- Document all config keys in `_docs/usage.md` and in this README.

---

## 📄 Documentation & Testing
- Place all best practices, diagrams, and usage guides in `_docs/`.
- All tests (unit, integration, smoke, ingestion) go in `_tests/` with clear naming.
- Use `_tests/_docs/` for test-specific docs if needed.

---

## 🐳 Docker & Provisioning
- Place Dockerfile(s), docker-compose, and provisioning configs in `docker/`.
- Provide `.env.example` for local/dev/prod setups.
- Use distributed mode for production-like ingestion tests.

---

## 📝 Repeatable Prompt/Template for Future Folders

```
@[<path/to/new_service>] create readme for this folder and suite @[<path/to/new_service/_tests/_docs/alerts.md>]@[<path/to/new_service/_tests/_docs/docker.md>]@[<path/to/new_service/_tests/_docs/infra.md>]@[<path/to/new_service/_tests/_docs/README.md>]  add it to the root, add docker folder, docs folder, tests etc and give me a prompt so I can repeat this action for future folders with the same structure. Include singleton structure and config.
```

- Replace `<path/to/new_service>` with your actual folder path.
- This will scaffold:
  - `README.md` (main)
  - `config.py` (singleton config)
  - `_docs/` (docs, best practices)
  - `_tests/` (tests)
  - `docker/` (container/provisioning)
  - `models/` (schemas)
  - `exceptions/` (custom errors)
  - Main implementation modules

---

## 📦 Usage

1. **Clone this repo or add as a submodule.**
2. Copy and configure the example Docker Compose and config files for your environment.
3. Set environment variables for all secrets and endpoints (see `.env.example`).
4. Launch the stack:
   ```bash
   docker-compose -f docker/docker-compose.test.yml --profile observability up -d
   ```
5. Run tests:
   ```bash
   pytest _tests/
   ```

## 📚 Documentation

- See [`_docs/best_practices/`](./_docs/best_practices/) for integration, config, and security guidance.
- Example configs: [`docker/`](./docker/)
- Test suite: [`_tests/`](./_tests/)

## 🛡️ Production-Readiness

- All configurations are type-checked and validated.
- No secrets are hardcoded; all sensitive data is environment-driven.
- Tests are deterministic, isolated, and CI/CD compatible.

---

**Author:** [TechWithTy](https://github.com/TechWithTy)

**License:** MIT
