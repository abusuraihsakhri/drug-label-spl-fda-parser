# Drug Label SPL FDA Parser

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** FDA Structured Product Labeling (SPL) XML, CAP / CLSI / ISO

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Drug Label SPL FDA Parser is an enterprise-grade analytical platform for evaluating clinical and biomedical task payloads. It processes structured task data through a multi-agent worker architecture, generating consensus dossiers with cryptographic audit trails.

The system provides:

- **Multi-Agent Evaluation**: Three specialized workers (InvariantQC, SafetyEscalation, ProtocolConformance) independently assess each task
- **Consensus Generation**: Aggregates worker alerts into a unified dossier with overall urgency classification
- **Cryptographic Audit Trail**: HMAC-SHA256 chained tamper-evident logging for every evaluation
- **Zero-PHI Outbound Guard**: Active pattern detection blocking protected health information from outbound content
- **FastAPI REST API**: OpenAPI 3.1 endpoints for programmatic access
- **Prometheus Metrics**: Operational telemetry export

---

## Architecture

```
drug-label-spl-fda-parser/
├── agents/                    # Core enterprise agent framework
│   ├── base.py               # PHI guard, HMAC audit trail, security exceptions
│   ├── models.py             # Pydantic v2 schemas (SystemTaskPayload, ConsensusDossier)
│   ├── workers.py            # Specialized evaluation workers
│   ├── supervisor.py         # Multi-agent orchestrator
│   ├── api.py                # FastAPI REST endpoints
│   ├── metrics.py            # Prometheus metrics exporter
│   ├── learning.py           # Bayesian calibration engine
│   ├── streamer.py           # WebSocket telemetry broadcaster
│   └── llm_factory.py        # LLM provider abstraction
├── spl_label_parser/          # Alternative SPL-focused implementation
│   ├── models.py             # Frontier data models
│   ├── agents.py             # SPL-specific coordination agents
│   ├── engine.py             # Core evaluation engine
│   ├── server.py             # FastAPI server factory
│   └── cli.py                # SPL-specific CLI
├── tests/                     # Pytest test suite
├── web/                       # Operations console (HTML/JS)
├── cli.py                     # Main CLI entry point
├── enrichment.py              # Domain enrichment engines
├── simulator.py               # High-throughput stress testing
└── pyproject.toml             # Project configuration
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/drug-label-spl-fda-parser.git
cd drug-label-spl-fda-parser

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set required environment variable for audit trail
export AUDIT_SECRET_KEY=$(openssl rand -hex 32)
```

---

## Usage

### CLI Commands

#### Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

#### Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

#### Verify Audit Trail
```bash
python cli.py verify-audit
```

#### Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check and system metadata |
| `/metrics` | GET | Prometheus operational metrics |
| `/api/audit` | POST | Submit task for multi-agent evaluation |
| `/api/chat` | POST | Supervisory conversational query |
| `/api/audit/logs` | GET | Retrieve and verify HMAC audit trail |

### Input Data Schema

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `task_id` | string | Unique task/case identifier | Yes |
| `target_identifier` | string | Entity or target key | Yes |
| `primary_metric` | float | Primary measurement or score (finite) | Yes |
| `secondary_metric` | float | Secondary kinetic/confidence score (finite) | No (default: 0.0) |
| `status_descriptor` | string | Status code or phenotype descriptor | No (default: "NOMINAL") |
| `is_critical_flag` | boolean | Emergency escalation trigger | No (default: false) |

---

## Security

### Zero-PHI Outbound Guard
Active regex-based detection blocks outbound content containing:
- Medical Record Numbers (MRN)
- Social Security Numbers (SSN)
- Phone numbers and email addresses
- Date of birth patterns
- Patient name patterns

### HMAC-SHA256 Audit Trail
- Every evaluation and state transition is cryptographically signed
- Chained hash structure detects tampering
- Requires `AUDIT_SECRET_KEY` environment variable (minimum 16 characters)

### Input Validation
- Metric values must be finite (NaN/Infinity rejected)
- Identifier fields must be non-empty
- PHI patterns blocked in all outbound content

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=spl_label_parser

# Run simulation benchmark
python simulator.py --tasks 1000
```

---

## Docker Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY=$(openssl rand -hex 32)
docker-compose up --build

# Or use Docker directly
docker build -t drug-label-spl-fda-parser .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$AUDIT_SECRET_KEY drug-label-spl-fda-parser
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
