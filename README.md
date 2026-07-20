# Kubernetes AI Assistant

This project is an intelligent Kubernetes assistant that automatically analyzes incidents on your pods. 
It extracts pod context (logs, events, container state), applies basic analysis rules, and uses an LLM (Large Language Model) to generate a detailed summary of the incident, deduce the root cause, and propose remediation commands.

>>>> Développement d'un assistant SRE basé sur l'IA pour l'analyse automatique d'incidents Kubernetes, avec moteur de règles, intégration LLM, API REST et architecture modulaire."

## Prerequisites

- **Python 3.8+**
- A functional Kubernetes cluster (e.g., minikube, Docker Desktop, etc.)
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
   kubectl apply -f test-app.yml
   ```
2. Wait a few seconds for the pod to fail, then run the analysis:
   ```bash
   python main.py
   ```
3. The assistant will analyze the logs and display a detailed summary of the situation along with proposed solutions.

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

## Switching from Ollama to OpenAI for Production

By default, this project uses **Ollama** locally to avoid API costs and ensure data privacy during development.
However, for a production deployment, it is recommended to switch to a more robust and managed model like those provided by **OpenAI**.

Here is how to modify the project to use OpenAI:

1. **Add your API key**  
   Create a `.env` file at the root of the project and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=sk-your-api-key
   ```

2. **Modify the `ai.py` file**  
   Use the official OpenAI SDK (already included in `requirements.txt`) instead of the `requests` call to `localhost`. 

   Example modification for `ai.py`:
   ```python
   import os
   from openai import OpenAI
   from dotenv import load_dotenv

   load_dotenv()
   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

   def analyze_logs(incident, findings):
       ffindings = "\n".join([f"[{f['severity'].upper()}] {f['message']}" for f in findings])

       prompt = f"""
       You are a senior SRE engineer.
       Here is the context: {incident}
       Here are the automatic findings: {ffindings}
       ... (rest of your prompt) ...
       """

       response = client.chat.completions.create(
           model="gpt-4o-mini", # Suitable model for production
           messages=[
               {"role": "user", "content": prompt}
           ]
       )

       return response.choices[0].message.content
   ```

3. **Privacy in production**: Ensure you filter or anonymize sensitive logs (passwords, tokens) before sending them to the OpenAI API.

