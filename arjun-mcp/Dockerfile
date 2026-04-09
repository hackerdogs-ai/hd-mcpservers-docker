# Arjun MCP - Hackerdogs Ready
FROM python:3.12-slim-bookworm
RUN groupadd -g 1000 mcpuser && useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/s0md3v/Arjun /opt/arjun && chmod -R a+rX /opt/arjun
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py ./
RUN chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONUNBUFFERED=1 MCP_TRANSPORT=stdio MCP_PORT=8383 ARJUN_CMD="python3 /opt/arjun/arjun.py"
EXPOSE 8383
CMD ["python", "mcp_server.py"]
