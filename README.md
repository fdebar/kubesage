# Kubernetes AI Assistant

This project is an intelligent Kubernetes assistant that automatically analyzes incidents on your pods. 
It extracts pod context (logs, events, container state), applies basic analysis rules, and uses an LLM (Large Language Model) to generate a detailed summary of the incident, deduce the root cause, and propose remediation commands.

## Prerequisites

- **Python 3.8+**
- A functional Kubernetes cluster (e.g., Minikube, Docker Desktop, AWS EKS etc.)
- **Ollama** installed locally with the `llama3.1` model downloaded (`ollama run llama3.1`)

## Installation

1. Clone the project and navigate to the directory.
2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

The project includes a test manifest (`test-app.yml`) that deploys a failing pod (database and Redis connection errors).

1. Deploy the test pod to your cluster:
```bash
kubectl apply -f tests/test-app.yml
```

2. Wait a few seconds for the pod to fail, then run the analysis:
```bash
python main.py
```

3. The assistant will analyze the logs and output a detailed JSON report of the situation, including the severity, summary, root cause, recommendations, and useful kubectl commands.

## Project Structure

                +------------------+
                | CLI / API / Slack|
                +---------+--------+
                          |
                          v
                 Incident Service
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
   Kubernetes      Rule Engine      Prometheus
          |               |
          +-------+-------+
                  |
                  v
              AI Service
                  |
                  v
            GPT / Ollama


- `k8s.py`: Interacts with the Kubernetes API to retrieve the context, events, and logs of the pod.
- `rules.py`: Analyzes the raw context to extract findings programmatically.
- `ai.py`: Sends the findings and context to Ollama (LLM) for a human-readable analysis.
- `main.py`: The main entry point of the program.
- `test-app.yml`: A Kubernetes test manifest generating intentional errors.

---

## Running tests

Using virtual environment:

```bash
source .venv/bin/activate
python -m pytest   
deactivate
```

## Switching from Ollama to OpenAI for Production

By default, this project uses **Ollama** locally to avoid API costs and ensure data privacy during development.
However, for a production deployment, it is recommended to switch to a more robust and managed model like those provided by **OpenAI**.

The project natively supports OpenAI. Here is how to configure it:

1. **Add your API key and Model**  
   Create a `.env` file at the root of the project and set your OpenAI API key and desired model:
   ```env
   OPENAI_API_KEY=sk-your-api-key
   OPENAI_MODEL=gpt-4o-mini
   ```

2. **Run the analysis**  
   The application will automatically detect the `OPENAI_API_KEY` and use the official OpenAI API instead of the local Ollama instance. The output format remains a structured JSON report.

3. **Privacy in production**: Ensure you filter or anonymize sensitive logs (passwords, tokens) before sending them to the OpenAI API.

