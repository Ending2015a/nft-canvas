#!/bin/bash
DOCKER_NAME="ending2015a/usd-from-gltf:latest"

docker run --rm \
    -v $(pwd):/usr/app \
    -p 8000:8000 \
    --entrypoint "/bin/bash" \
    $DOCKER_NAME \
    -c "cd src/ ; uvicorn app:app --reload --port 8000 --host 0.0.0.0"

