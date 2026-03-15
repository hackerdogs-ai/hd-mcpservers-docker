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

# Install ujson and other dependencies first (needed by theHarvester)
RUN pip install --no-cache-dir ujson aiomultiprocess netaddr aiohttp && \
    pip install --no-cache-dir censys || true && \
    pip install --no-cache-dir shodan || true && \
    pip install --no-cache-dir git+https://github.com/0xInfection/aiosqli.git || pip install --no-cache-dir aiosqli || echo "aiosqli optional"

# Copy patch scripts (files should be in service directory for publishing)
# For docker-compose, these are copied from parent directory
COPY fix_aiosqli.py /tmp/fix_aiosqli.py
COPY patch_theharvester.py /tmp/patch_theharvester.py

# Install theHarvester via pip (handles dependencies better)
RUN pip install --no-cache-dir theharvester && \
    git clone --depth 1 https://github.com/laramies/theHarvester.git /opt/theharvester && \
    cd /opt/theharvester && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir aiosqlite uvloop pyyaml aiohttp netaddr || true && \
    (pip install --no-cache-dir git+https://github.com/0xInfection/aiosqli.git 2>&1 || \
     pip install --no-cache-dir aiosqli 2>&1 || \
     (echo "Installing aiosqli from alternative source" && \
      git clone --depth 1 https://github.com/0xInfection/aiosqli.git /tmp/aiosqli && \
      cd /tmp/aiosqli && pip install --no-cache-dir . 2>&1 || \
      (python3 -c "import os, site; sp=site.getsitepackages()[0] if site.getsitepackages() else '/usr/local/lib/python3.11/site-packages'; os.makedirs(f'{sp}/aiosqli', exist_ok=True); f=open(f'{sp}/aiosqli/__init__.py','w'); f.write('class AioSQLi:\\n    def __init__(self,*a,**k):pass\\n    def scan(self,*a,**k):return[]\\n    async def scan_async(self,*a,**k):return[]\\n'); f.close(); print('Created aiosqli dummy')"))) && \
    cd /opt/theharvester && \
    python3 /tmp/fix_aiosqli.py && \
    find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && \
    find . -name "*.pyc" -delete 2>/dev/null || true && \
    chmod +x theHarvester.py 2>/dev/null || true

# Copy server files (relative to service directory)
COPY src/theharvester_mcp_server.py /app/src/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Make the server executable
RUN chmod +x /app/src/theharvester_mcp_server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Verify installation
RUN test -f /opt/theharvester/theHarvester.py && echo "✓ theHarvester found"

# Run the MCP server
ENTRYPOINT ["python3", "/app/src/theharvester_mcp_server.py"]

