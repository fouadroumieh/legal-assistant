# nlpapi/Dockerfile (build context = nlpapi/)
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Put the whole context under /app/nlpapi to keep package path
COPY . /app/nlpapi

ENV PYTHONPATH=/app
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "nlpapi.main:app", "--host", "0.0.0.0", "--port", "8080"]
