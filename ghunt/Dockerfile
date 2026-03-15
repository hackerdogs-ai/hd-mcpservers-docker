FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone and install GHunt
RUN git clone --depth 1 https://github.com/mxrch/GHunt.git /opt/ghunt && \
    cd /opt/ghunt && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir packaging && \
    pip install --no-cache-dir -e . 2>/dev/null || pip install --no-cache-dir . 2>/dev/null || true && \
    chmod +x main.py ghunt.py 2>/dev/null || true && \
    ln -s /opt/ghunt/main.py /usr/local/bin/ghunt 2>/dev/null || true

# Copy server files
COPY src/ghunt_mcp_server.py /app/src/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Make the server executable
RUN chmod +x /app/src/ghunt_mcp_server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/ghunt:${PATH}"

# Verify installation
RUN ls -la /opt/ghunt/ | head -5 && test -d /opt/ghunt && echo "✓ GHunt directory found"

# Run the MCP server
ENTRYPOINT ["python3", "/app/src/ghunt_mcp_server.py"]

