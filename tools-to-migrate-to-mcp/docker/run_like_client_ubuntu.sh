#!/usr/bin/env bash
# Run osint-tools on Ubuntu the same way the client (DockerOSINTClient / exiftool LangChain tool) does.
# Use this to verify the container and exiftool flow without running the full chat stack.
#
# Client behavior (from docker_client.py + exiftool_langchain.py):
#   - Image: OSINT_DOCKER_IMAGE or hackerdogs/osint-tools:latest
#   - Container name: osint-tools
#   - Workspace: /tmp/osint-workspace on host → /workspace in container
#   - docker run -d --name osint-tools -v /tmp/osint-workspace:/workspace --restart unless-stopped <image>
#   - For exiftool: docker cp <file> osint-tools:/workspace/<name> then docker exec -w /workspace osint-tools exiftool ...
#
# Usage (from repo root or from shared/modules/tools/docker):
#   ./shared/modules/tools/docker/run_like_client_ubuntu.sh
#   ./shared/modules/tools/docker/run_like_client_ubuntu.sh build   # build image locally instead of pull

set -e

CONTAINER_NAME="osint-tools"
WORKSPACE_HOST="/tmp/osint-workspace"
WORKSPACE_CONTAINER="/workspace"
IMAGE="${OSINT_DOCKER_IMAGE:-hackerdogs/osint-tools:latest}"

# Optional: build from repo instead of pull
DO_BUILD=false
if [[ "${1:-}" == "build" ]]; then
  DO_BUILD=true
fi

echo "=== Run osint-tools like the client on Ubuntu ==="
echo "  Image: $IMAGE"
echo "  Container: $CONTAINER_NAME"
echo "  Host workspace: $WORKSPACE_HOST -> container $WORKSPACE_CONTAINER"
echo ""

# 1) Image: pull or build
if [[ "$DO_BUILD" == "true" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$SCRIPT_DIR"
  echo "Building image (from repo)..."
  docker build -t osint-tools:latest .
  IMAGE="osint-tools:latest"
else
  echo "Pulling image..."
  docker pull "$IMAGE" || { echo "Pull failed; try: $0 build"; exit 1; }
fi

# 2) Workspace (same as client)
mkdir -p "$WORKSPACE_HOST"

# 3) Create/start container exactly like DockerOSINTClient
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Container $CONTAINER_NAME already exists; starting if needed..."
  docker start "$CONTAINER_NAME" 2>/dev/null || true
else
  echo "Creating container (same as client)..."
  docker run -d \
    --name "$CONTAINER_NAME" \
    -v "$(cd "$WORKSPACE_HOST" && pwd):$WORKSPACE_CONTAINER" \
    --restart unless-stopped \
    "$IMAGE"
fi

echo ""
echo "Container running. Testing exiftool like the client..."

# 4) Simulate exiftool flow: put a file in workspace, then docker exec exiftool
SAMPLE_URL="https://github.com/ianare/exif-samples/raw/master/jpg/gps/DSCN0010.jpg"
LOCAL_FILE="$WORKSPACE_HOST/sample_$(date +%s).jpg"
CONTAINER_FILE="$WORKSPACE_CONTAINER/$(basename "$LOCAL_FILE")"

echo "  Downloading sample image to $LOCAL_FILE"
wget -q -O "$LOCAL_FILE" "$SAMPLE_URL" || { echo "wget failed"; exit 1; }

echo "  Copying into container (docker cp)..."
docker cp "$LOCAL_FILE" "$CONTAINER_NAME:$CONTAINER_FILE"

echo "  Running exiftool in container (docker exec -w $WORKSPACE_CONTAINER osint-tools exiftool ...)..."
docker exec -w "$WORKSPACE_CONTAINER" "$CONTAINER_NAME" exiftool "$CONTAINER_FILE"

echo ""
echo "=== Done (client-like run). Container left running as '$CONTAINER_NAME'. ==="
echo "  Stop: docker stop $CONTAINER_NAME"
echo "  Remove: docker rm -f $CONTAINER_NAME"
