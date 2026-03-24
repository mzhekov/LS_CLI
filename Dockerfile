# ---- build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt gunicorn


# ---- runtime stage ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Install the leadsauce package itself (no deps — already installed above)
RUN pip install --no-cache-dir --no-deps .

# The app reads/writes ~/.leadsauce — for root that resolves to /root/.leadsauce.
# We create it here; the actual directory is bind-mounted from the host at runtime
# so the container shares the same SQLite database as the CLI.
RUN mkdir -p /root/.leadsauce/logs

EXPOSE 5055

# 2 sync workers is plenty for a personal assistant API.
# --timeout 300  gives Ollama time to load the model and generate a response.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5055", \
     "--workers", "2", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "wsgi:app"]
