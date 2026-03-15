# Multi-OSINT Tools Docker Image
# Contains all OSINT binary tools in a single container

FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3 \
    python3-pip \
    ca-certificates \
    gnupg \
    lsb-release \
    libpcap-dev \
    libyara-dev \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

# Install Go (required for Go-based tools)
ENV GO_VERSION=1.21.5
# Detect architecture and install appropriate Go version
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        GO_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        GO_ARCH="arm64"; \
    else \
        GO_ARCH="amd64"; \
    fi && \
    wget -q https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-${GO_ARCH}.tar.gz && \
    rm go${GO_VERSION}.linux-${GO_ARCH}.tar.gz
ENV PATH=$PATH:/usr/local/go/bin

# Disable CGO to avoid cross-compilation issues (especially on ARM64/Apple Silicon)
# Most Go tools work fine without CGO
ENV CGO_ENABLED=0

# Install remaining system packages (combine to reduce layers)
RUN apt-get update && apt-get install -y \
    masscan \
    zmap \
    yara \
    && rm -rf /var/lib/apt/lists/*

# Set Go environment and prepare for tool installation
ENV PATH=$PATH:/root/go/bin
ENV GOPATH=/root/go
ENV GO111MODULE=on

# Install Go tools with optimized approach
# CRITICAL FIX: Changed from building all packages (v4/...@master) to just the binary (v4/cmd/amass@v4.2.0)
# This reduces build time from hours to ~10-15 minutes by:
# 1. Using stable version (@v4.2.0) instead of @master (avoids compiling latest dev code)
# 2. Installing only the binary (cmd/amass) instead of all packages (...)
# 3. Combining all Go installs into one RUN layer for better caching
RUN echo "Installing Go tools (this may take 10-15 minutes)..." && \
    # Install Amass - CRITICAL: Use specific version and only the binary, not all packages
    go install -v github.com/owasp-amass/amass/v4/cmd/amass@v4.2.0 && \
    # Install Nuclei - use latest stable
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    # Install Subfinder
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    # Install waybackurls
    go install github.com/tomnomnom/waybackurls@latest && \
    echo "✅ Go tools installation complete!"

# Install ExifTool (already installed via libimage-exiftool-perl)
# Verify it's available as exiftool command

# Install Python OSINT tools
RUN pip3 install --no-cache-dir \
    sublist3r \
    dnsrecon \
    dnspython \
    python-nmap \
    theHarvester \
    sherlock-project \
    maigret \
    ghunt \
    holehe \
    onionsearch \
    scrapy \
    waybackpy \
    internetarchive \
    requests[socks] \
    pysocks \
    stem \
    exifread \
    piexif \
    yara-python

# Create working directory
WORKDIR /workspace

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (keeps container running)
CMD ["tail", "-f", "/dev/null"]

# Labels
LABEL maintainer="hackerdogs.ai"
LABEL description="Multi-OSINT tools container with Amass, Nuclei, Subfinder, Masscan, ZMap, and Python OSINT tools"
LABEL version="1.0"

