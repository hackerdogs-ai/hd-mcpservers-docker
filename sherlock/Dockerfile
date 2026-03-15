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

# Install Sherlock
RUN pip install --no-cache-dir sherlock-project

# Copy server files
COPY src/sherlock_mcp_server.py /app/src/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Make the server executable
RUN chmod +x /app/src/sherlock_mcp_server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Verify installation
RUN which sherlock && echo "✓ Sherlock found"

# Run the MCP server
ENTRYPOINT ["python3", "/app/src/sherlock_mcp_server.py"]

