#!/bin/bash

# Quick script to tag and push the PDF reader image to Docker Hub
# Use this if the image was built but not pushed

set -e

DOCKER_HUB_USERNAME="hackerdogs"
LOCAL_IMAGE="hackerdogs-mcp-pdf-reader-sylphx:latest"
DOCKERHUB_IMAGE="${DOCKER_HUB_USERNAME}/${LOCAL_IMAGE}"

echo "Tagging ${LOCAL_IMAGE} as ${DOCKERHUB_IMAGE}..."
docker tag "${LOCAL_IMAGE}" "${DOCKERHUB_IMAGE}"

if [ $? -eq 0 ]; then
    echo "✅ Tagged successfully"
else
    echo "❌ Failed to tag"
    exit 1
fi

echo "Pushing ${DOCKERHUB_IMAGE} to Docker Hub..."
docker push "${DOCKERHUB_IMAGE}"

if [ $? -eq 0 ]; then
    echo "✅ Pushed successfully"
    echo ""
    echo "Image is now available at:"
    echo "  https://hub.docker.com/r/${DOCKER_HUB_USERNAME}/hackerdogs-mcp-pdf-reader-sylphx"
else
    echo "❌ Failed to push"
    exit 1
fi


