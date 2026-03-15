#!/bin/bash
# Build and run OSINT tools Docker container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🐳 Building OSINT Tools Docker Image..."
docker build -t osint-tools:latest .

echo ""
echo "✅ Build complete!"
echo ""
echo "Starting container..."

# Create workspace directory if it doesn't exist
mkdir -p workspace results

# Start container
docker-compose up -d

echo ""
echo "✅ Container started!"
echo ""
echo "To check status:"
echo "  docker ps | grep osint-tools"
echo ""
echo "To test a tool:"
echo "  docker exec osint-tools amass -version"
echo ""
echo "To view logs:"
echo "  docker logs osint-tools"
echo ""
echo "To stop container:"
echo "  docker-compose down"

