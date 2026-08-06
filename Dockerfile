# ---------- Builder ----------
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv

COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade .

COPY . .

RUN pip install --no-cache-dir .

# ---------- Runtime ----------
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN addgroup --system kubesage && \
    adduser --system --ingroup kubesage kubesage

COPY --from=builder /opt/venv /opt/venv
COPY --chown=kubesage:kubesage . /app/

# Remove system-level packages from the base python image
RUN rm -rf /usr/local/lib/python3.14/site-packages/pip* \
           /usr/local/lib/python3.14/site-packages/setuptools* \
           /usr/local/lib/python3.14/site-packages/msgpack* \
           /opt/venv/lib/python3.14/site-packages/pip* \
           /opt/venv/lib/python3.14/site-packages/setuptools* \
           /opt/venv/lib/python3.14/site-packages/wheel*

USER kubesage

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD []
