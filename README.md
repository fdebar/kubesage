# 🚀 KubeSage

![CI](https://github.com/fdebar/KubeSage/actions/workflows/ci.yml/badge.svg)

> AI-powered Kubernetes incident analysis assistant for DevOps and SRE teams.

KubeSage is an intelligent Kubernetes troubleshooting assistant designed to accelerate incident investigation by combining:

* Kubernetes data collection
* Prometheus metrics
* Rule-based diagnostics
* Structured findings
* Large Language Models (LLMs)

Instead of simply summarizing logs, KubeSage correlates operational signals to identify probable root causes and generate actionable recommendations.

The goal is simple:

**Reduce the time required to understand and troubleshoot Kubernetes incidents.**

---

# Why KubeSage?

Modern Kubernetes troubleshooting often requires switching between multiple tools:

* `kubectl`
* Application logs
* Kubernetes events
* Prometheus dashboards
* Resource metrics
* Monitoring tools

KubeSage automates this workflow by collecting, correlating and explaining operational data in a single structured incident report.

The AI component does not replace deterministic diagnostics. It enhances them by providing context-aware explanations and recommendations.

---

# Features

## Kubernetes Analysis

* 🔍 Pod information collection
* 📜 Application log analysis
* 📅 Kubernetes events retrieval
* 📊 Resource usage collection through Metrics Server

## Observability

* 📈 Prometheus metrics integration
* 🔎 Metrics correlation with incidents
* 📝 Structured operational logging
* 🆔 Request ID tracing

## Diagnostic Engine

* 🧠 Rule-based incident detection
* 🔌 Plugin architecture for custom diagnostic rules
* 📋 Structured findings
* 🎯 Confidence scoring

## AI Analysis

* 🧩 Context aggregation
* 📝 Prompt generation
* 🤖 LLM-powered incident explanation
* 🛠 Actionable kubectl recommendations

## Developer Experience

* 💻 CLI interface
* 🌐 REST API with FastAPI
* ✅ Automated tests
* 🔍 Static analysis
* 🧹 Code formatting

---

# Architecture

```
                           +----------------+
                           |    CLI / API   |
                           +--------+-------+
                                    |
                                    |
                         +----------v-----------+
                         |   IncidentService   |
                         +----------+-----------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        |                           |                           |
+-------v-------+          +--------v--------+        +---------v---------+
| Kubernetes API|          | Metrics Server  |        |    Prometheus     |
+---------------+          +-----------------+        +-------------------+
                                    |
                                    |
                         +----------v-----------+
                         |      Incident       |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         | Diagnostic Engine   |
                         +----------+-----------+
                                    |
                            Plugin Rules
                                    |
                         +----------v-----------+
                         |     Findings        |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         |  Context Builder    |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         |  Prompt Builder     |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         |    AI Service       |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         |    AI Report        |
                         +---------------------+
```

---

# Project Structure

```
kubesage/

├── analyzers/
│   ├── diagnostic_engine.py
│   └── rules/
│
├── builders/
│   ├── context_builder.py
│   └── prompt_builder.py
│
├── models/
│   ├── incident.py
│   ├── finding.py
│   ├── ai_context.py
│   ├── ai_report.py
│   └── prometheus.py
│
├── services/
│   ├── ai_service.py
│   ├── incident_service.py
│   ├── kubernetes_service.py
│   ├── metrics_service.py
│   └── prometheus_service.py
│
├── api/
│   └── routes/
│
├── tests/
│
├── config.py
├── exceptions.py
├── logging_config.py
├── main.py
└── README.md
```

---

# Technology Stack

## Backend

* Python 3.12+
* FastAPI
* Kubernetes Python Client
* Requests
* Pytest

## Observability

* Prometheus
* Kubernetes Metrics Server
* Structured logging

## AI

* OpenAI API
* Ollama local development environment
* LLM prompt engineering

## Development

* Ruff
* MyPy
* Makefile automation

---

# Prerequisites

Before running KubeSage, ensure:

* Python 3.12+
* Kubernetes cluster
* `kubectl` configured
* Metrics Server installed
* Prometheus installed

For production:

* OpenAI API key

For local development:

* Ollama running with a compatible model

---

# Installation

Clone the repository:

```bash
git clone https://github.com/<your-account>/kubesage.git
cd kubesage
```

Create the environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -e .
```

---

# Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.5

PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_TIMEOUT=5

KUBERNETES_NAMESPACE=default

LOG_LEVEL=INFO
```

---

# Running

## CLI

Analyze a Kubernetes pod:

```bash
kubesage analyze --pod ai-demo-app
```

Example:

```
Collecting Kubernetes data...
Collecting Prometheus metrics...
Running diagnostic rules...
Generating AI analysis...

Analysis completed.
```

---

## API

Start the REST API:

```bash
uvicorn api.app:app --reload
```

Example request:

```http
POST /analyze
```

```json
{
  "namespace": "default",
  "pod": "ai-demo-app"
}
```

Example response:

```json
{
  "summary": "Application cannot connect to Redis",
  "severity": "critical",
  "findings": [
    {
      "type": "connection_error",
      "confidence": 0.92
    }
  ],
  "kubectl_commands": [
    "kubectl describe pod ai-demo-app"
  ]
}
```

---

# Observability

KubeSage exposes operational information through:

## Logs

Structured logs include:

* request_id
* namespace
* pod
* execution status
* errors

## Metrics

Prometheus metrics include:

* API request duration
* Analysis count
* Error count
* AI processing latency

---

# Example Workflow

```
User Request

      |
      v

CLI / REST API

      |
      v

Incident Collection

      |
      +----------------+
      |                |
      v                v

Kubernetes       Prometheus
Data             Metrics

      |
      v

Diagnostic Engine

      |
      v

Findings

      |
      v

Context Builder

      |
      v

Prompt Builder

      |
      v

LLM Analysis

      |
      v

Incident Report
```

---

# Development Commands

Using Makefile:

```bash
make test

make lint

make format

make check

make fix

make dev-run

make dev-stop
```

---

# Testing

Run tests:

```bash
pytest
```

On macOS:

```bash
python -m pytest
```

---

# Code Quality

Format:

```bash
ruff format .
```

Lint:

```bash
ruff check .
```

Type checking:

```bash
mypy .
```

---

# Roadmap

## Completed

✅ Project architecture
✅ CLI interface
✅ Structured logging
✅ Unit tests
✅ Diagnostic engine
✅ Plugin rules
✅ OpenAI integration
✅ Metrics Server integration
✅ Prometheus integration
✅ Context Builder
✅ Prompt Builder
✅ AI Report generation
✅ FastAPI REST API

---

## Next Steps

🚧 Slack / Microsoft Teams integration

🚧 Docker image

🚧 Helm deployment

🚧 GitHub Actions CI/CD

🚧 Grafana dashboard

🚧 Loki integration

🚧 Alertmanager integration

🚧 Multi-cluster support

🚧 Web dashboard

---

# Design Principles

KubeSage follows several principles:

* Deterministic diagnostics before AI reasoning
* Structured outputs over free-form responses
* AI as an assistant, not an autonomous operator
* Extensible architecture through plugins
* Production-oriented engineering practices

---

# Future Improvements

* Historical incident comparison
* Incident timeline visualization
* Root Cause Analysis graph
* AI-generated remediation plans
* Optional auto-remediation workflows

---

# Contributing

Contributions are welcome.

Before submitting major changes:

1. Open an issue
2. Create a feature branch
3. Add tests
4. Submit a Pull Request

---

# License

MIT License.

---

# Author

Developed as an engineering project exploring the intersection of:

* Kubernetes
* DevOps
* Site Reliability Engineering
* Artificial Intelligence
* Large Language Models
