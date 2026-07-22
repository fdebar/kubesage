FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir .

COPY . .

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

USER appuser

EXPOSE 8000

CMD ["uvicorn", "kubesage.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
