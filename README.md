<h1 align="center">🤖 KubeSage</h1>

<p align="center">
  <img src="docs/kubesage-logo.png" alt="KubeSage Logo" width="280">
</p>

<p align="center">
AI-powered Kubernetes Operations Assistant
</p>

<p align="center">
Observe • Explain • Recommend • Act
</p>

<h4 align="center">

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Helm](https://img.shields.io/badge/Helm-3-0F1689)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Enabled-6F2DBD)
![Grafana](https://img.shields.io/badge/Grafana-Observability-F46800)
![License](https://img.shields.io/badge/License-MIT-green)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)
![Ruff](https://img.shields.io/badge/Ruff-Linting-D7FF64)
![MyPy](https://img.shields.io/badge/MyPy-Type_Checked-2A6DB0)

</h4>

<h4 align="center">

![Code Quality Checks](https://github.com/fdebar/KubeSage/actions/workflows/ci.yml/badge.svg)
![Docker](https://github.com/fdebar/KubeSage/actions/workflows/docker.yml/badge.svg)
![Helm](https://github.com/fdebar/KubeSage/actions/workflows/helm.yml/badge.svg)

</h4>

KubeSage is an intelligent Kubernetes troubleshooting assistant designed to accelerate incident investigation by combining:

* Kubernetes data collection
* Prometheus metrics
* Rule-based diagnostics
* Structured findings
* Large Language Models (LLMs)

Instead of simply summarizing logs, KubeSage correlates operational signals to identify probable root causes and generate actionable recommendations.

The goal is simple:

**Reduce the time required to understand and troubleshoot Kubernetes incidents.**

# 🚀 Quick Start

```bash
git clone https://github.com/fdebar/KubeSage.git

cd KubeSage

helm install kubesage deploy/kubesage \
    -n kubesage \
    --create-namespace
```

Analyze a pod:

```bash
kubesage analyze --namespace default --pod nginx
```

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

# 🏗️ Architecture

<img src="docs/architecture.png" alt="KubeSage Architecture" />

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
* 📦 Helm Chart
* 🚀 One-command Kubernetes deployment
* 🔄 Environment-specific configuration
* ✅ Automated tests
* 🔍 Static analysis
* 🧹 Code formatting

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

* Python 3.14+
* FastAPI
* Kubernetes Python Client
* Requests
* Pytest

## Observability

* Grafana Alloy
* Prometheus
* Loki
* Tempo
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

Before installing KubeSage, ensure the following components are available.

## Kubernetes

* Python 3.14+
* Kubernetes 1.30+ cluster
* `kubectl` configured and connected to the target cluster
* Metrics Server installed
* Prometheus installed

Verify your cluster:

```bash
kubectl cluster-info
kubectl get nodes
kubectl top nodes
```

## Observability stack

KubeSage relies on a standard observability stack.

Required components:

* Grafana Alloy
* Prometheus
* Loki
* Tempo

The recommended installation method is Helm.
You can use [Grafana Cloud](https://grafana.com/products/cloud/) for a production deployment.

## AI Provider

KubeSage supports multiple AI backends.

### OpenAI (recommended)

Provide an API key:

```bash
OPENAI_API_KEY=<your_api_key>
```

### Ollama (local development)

Install and start Ollama, then pull a compatible model:

```bash
ollama pull llama3
```

### Helm

Helm is the recommended deployment method.

Verify your installation:

```bash
helm version
```

### Install KubeSage

Deploy KubeSage using Helm:

helm upgrade --install kubesage \
    deploy/kubesage \
    --namespace kubesage \
    --create-namespace \
    -f deploy/kubesage/values.yaml

Verify the deployment:

```bash
kubectl get pods -n kubesage
kubectl get svc -n kubesage
```

### Local development

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -e .
```

Run the CLI:

```bash
kubesage analyze \
    --namespace default \
    --pod ai-demo-app
````

Or start the REST API:

```bash
uvicorn kubesage.api.app:app --reload
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

# Example Analysis

```bash
$ kubesage analyze --namespace production --pod payment-api

✔ Kubernetes context collected
✔ Metrics retrieved
✔ Logs analyzed
✔ Traces correlated

Severity: HIGH

Root cause:
OOMKilled after 12 restarts.

AI explanation:
The application exceeds its memory limit during startup.

Recommendations:
• Increase memory limit to 1Gi.
• Investigate recent deployment changes.
• Check JVM heap configuration.

Confidence: 94%
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

| Feature | Status |
|----------|--------|
| CLI | ✅ |
| REST API | ✅ |
| Helm Chart | ✅ |
| Grafana Integration | ✅ |
| Prometheus | ✅ |
| Loki | ✅ |
| Tempo | ✅ |
| Grafana Alloy | ✅ |
| Docker Scout | ✅ |
| GitHub Actions | ✅ |
| GitOps | 🚧 |
| Auto-remediation | 🚧 |
| FinOps | 🚧 |

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
