FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m mcpuser && \
    mkdir -p /data /etc/caddy/dynamic && \
    chown -R mcpuser:mcpuser /data /etc/caddy
USER mcpuser
EXPOSE 9090
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9090"]
