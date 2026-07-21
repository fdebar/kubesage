# 🚀 KubeSage

> AI-powered Kubernetes incident analysis for DevOps and SRE teams.


KubeSage is an intelligent Kubernetes troubleshooting assistant that combines Kubernetes APIs, Prometheus metrics, rule-based diagnostics, and Large Language Models (LLMs) to accelerate incident investigation.

Instead of simply summarizing logs, KubeSage correlates data from multiple sources to identify probable root causes and generate actionable recommendations.

---

# Features

- 🔍 Collect Kubernetes pod information
- 📜 Analyze application logs
- 📅 Retrieve Kubernetes events
- 📈 Query Prometheus metrics
- 📊 Collect Metrics Server resource usage
- 🧠 Rule-based diagnostic engine
- 🤖 AI-powered incident explanation
- 🔌 Plugin architecture for custom diagnostic rules
- 📋 Structured findings with confidence scores
- 🛠 Actionable kubectl recommendations

---

# Architecture

```
                       +----------------------+
                       |       CLI/API        |
                       +----------+-----------+
                                  |
                                  |
                      +-----------v-----------+
                      |    IncidentService    |
                      +-----------+-----------+
                                  |
      +---------------------------+---------------------------+
      |                           |                           |
      |                           |                           |
+-----v------+          +---------v--------+         +--------v--------+
| Kubernetes |          | Metrics Server   |         |   Prometheus    |
|     API    |          |                  |         |      API        |
+------------+          +------------------+         +-----------------+
                                  |
                                  |
                         +--------v--------+
                         |    Incident     |
                         +--------+--------+
                                  |
                                  |
                         +--------v--------+
                         | DiagnosticEngine|
                         +--------+--------+
                                  |
                           Plugin-based Rules
                                  |
                         +--------v--------+
                         |    Findings     |
                         +--------+--------+
                                  |
                         +--------v--------+
                         | ContextBuilder  |
                         +--------+--------+
                                  |
                         +--------v--------+
                         | PromptBuilder   |
                         +--------+--------+
                                  |
                         +--------v--------+
                         |   AI Service    |
                         +--------+--------+
                                  |
                         +--------v--------+
                         |   AI Report     |
                         +-----------------+
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
├── prompts/
│   └── sre_analysis.txt
│
├── services/
│   ├── ai_service.py
│   ├── incident_service.py
│   ├── kubernetes_service.py
│   ├── metrics_service.py
│   └── prometheus_service.py
│
├── tests/
│
├── config.py
├── logging_config.py
├── exceptions.py
├── main.py
│
└── README.md
```

---

# Technology Stack

- Python 3.14
- Kubernetes Python Client
- Prometheus
- Metrics Server
- OpenAI API (development with Ollama running locally with `llama3.1`)
- Requests
- Pytest
- Ruff
- MyPy

---

# Prerequisites

Before running the project, ensure the following components are available.

- Python 3.14+
- Kubernetes cluster
- kubectl configured
- Metrics Server installed
- Prometheus installed
- OpenAI API Key (production)

---

# Installation

Clone the repository.

```bash
git clone https://github.com/<your-account>/kubesage.git
cd kubesage
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate it.

Linux / macOS

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file.

```text
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.5
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_TIMEOUT=5
KUBERNETES_NAMESPACE=default
LOG_LEVEL=INFO
```

---

# Running

Analyze a pod.

```bash
python main.py --pod ai-demo-app
```

Example output.

```
Collecting Kubernetes data...
Collecting Prometheus metrics...
Running 12 diagnostic rules...
Generating AI analysis...
Analysis completed.
```

---

# Testing

Run all unit tests.

```bash
pytest
```

Note: In MacOS use `python -m pytest`

---

# Code Quality

Format code.

```bash
ruff format .
```

Static analysis.

```bash
ruff check .
```

Type checking.

```bash
mypy .
```

---

# Example Workflow

```
Kubernetes API
        │
        ▼
Incident Collection
        │
        ▼
Prometheus Metrics
        │
        ▼
Rule Engine
        │
        ▼
Findings
        │
        ▼
Context Builder
        │
        ▼
Prompt Builder
        │
        ▼
OpenAI
        │
        ▼
AI Report
```

---

# Roadmap

## ✅ Sprint 1

- Project architecture

## ✅ Sprint 2

- Logging
- CLI
- Tests

## ✅ Sprint 3

- Diagnostic engine
- Plugin system

## ✅ Sprint 4

- OpenAI integration

## ✅ Sprint 5

- Metrics Server integration

## ✅ Sprint 6

- Rule plugin architecture

## ✅ Sprint 7

- Prometheus integration
- Context Builder
- Prompt Builder
- AI Report generation
- Project stabilization

## 🚧 Sprint 8

- FastAPI REST API

## 🚧 Sprint 9

- Slack / Microsoft Teams integration

## 🚧 Sprint 10

- Docker
- Helm
- GitHub Actions
- CI/CD

## 🚧 Sprint 11

- Web dashboard

## 🚧 Sprint 12

- v1.0 Release

---

# Future Improvements

- Multi-cluster support
- Grafana integration
- Loki integration
- Alertmanager integration
- Root Cause Analysis graph
- AI-generated remediation plans
- Auto-remediation (optional)
- Historical incident comparison
- Incident timeline visualization

---

# Contributing

Contributions are welcome.

Please open an issue before submitting large changes.

1. Fork the repository
2. Create a feature branch
3. Add tests
4. Submit a Pull Request

---

# License

MIT License.

---

# Author

Developed as a learning project exploring the intersection of:

- Kubernetes
- DevOps
- Site Reliability Engineering (SRE)
- Artificial Intelligence
- Large Language Models
