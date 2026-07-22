#!/usr/bin/env bash

for service in ollama api prometheus
do
    if [ -f ".run/$service.pid" ]; then
        kill "$(cat .run/$service.pid)" || true
        rm ".run/$service.pid"
    fi
done

echo "✅ Development environment stopped."