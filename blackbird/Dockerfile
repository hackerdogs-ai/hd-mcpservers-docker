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

# Clone and install Blackbird
RUN git clone --depth 1 https://github.com/p1ngul1n0/blackbird.git /opt/blackbird && \
    cd /opt/blackbird && \
    pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /app/data && \
    echo '{}' > /app/data/wmn-data.json

# Copy server files
COPY src/blackbird_mcp_server.py /app/src/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Make the server executable
RUN chmod +x /app/src/blackbird_mcp_server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Verify installation
RUN ls -la /opt/blackbird/ | head -5 && test -d /opt/blackbird && echo "✓ Blackbird directory found"

# Run the MCP server
ENTRYPOINT ["python3", "/app/src/blackbird_mcp_server.py"]

