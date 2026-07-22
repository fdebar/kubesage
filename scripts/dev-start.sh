#!/usr/bin/env bash
set -e

mkdir -p .run

echo "🤖 Starting Ollama..."
ollama serve > .run/ollama.log 2>&1 &
echo $! > .run/ollama.pid

echo "🌐 Starting FastAPI..."
uvicorn kubesage.api.app:app --reload > .run/api.log 2>&1 &
echo $! > .run/api.pid

echo "📊 Starting Prometheus port-forward..."
kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring > .run/prometheus.log 2>&1 &
echo $! > .run/prometheus.pid

echo "Prometheus is running at: http://localhost:9090"
echo "FastAPI is running at:    http://localhost:8000/docs"
echo "Ollama is running at:     http://localhost:11434"

echo "⚠️ Don't forget to run 'make dev-stop' to stop all the services."