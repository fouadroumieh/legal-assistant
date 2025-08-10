# docapi/Dockerfile  (build context = docapi/)
FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
# requirements.txt is in the docapi/ folder (build context root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Key change: install the package under /app/docapi ---
# Put the WHOLE context (docapi/) inside /app/docapi
COPY . /app/docapi

# Make /app importable so "import docapi" works regardless of CWD
ENV PYTHONPATH=/app

# App Runner default port
ENV PORT=8080
EXPOSE 8080

# Start the package entrypoint
CMD ["uvicorn", "docapi.main:app", "--host", "0.0.0.0", "--port", "8080"]
