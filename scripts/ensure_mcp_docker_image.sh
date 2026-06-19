#!/bin/bash
# ensure_mcp_docker_image IMAGE PROJECT_DIR
# If the image is not present: try docker pull, then docker build -t IMAGE PROJECT_DIR.
# Exits 0 when the image is available, non-zero if both pull and build fail.
ensure_mcp_docker_image() {
  local image="$1"
  local dir="$2"
  if docker image inspect "$image" >/dev/null 2>&1; then
    return 0
  fi
  echo "  Image not found locally: $image" >&2
  echo "  Trying: docker pull $image" >&2
  if docker pull "$image" 2>/dev/null; then
    return 0
  fi
  echo "  Pull failed or unavailable; building: docker build -t $image $dir" >&2
  docker build -t "$image" "$dir"
}
