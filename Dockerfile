# ---------- Builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md requirements.txt ./
COPY kubesage ./kubesage

RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt  .

# ---------- Runtime ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system kubesage && \
    adduser --system --ingroup kubesage kubesage

COPY --from=builder /install /usr/local
COPY --chown=kubesage:kubesage . /app/

USER kubesage

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "kubesage.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
