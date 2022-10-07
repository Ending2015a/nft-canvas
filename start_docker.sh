#!/bin/bash
DOCKER_NAME="ending2015a/usd-from-gltf:latest"

docker run -it --rm \
    -v $(pwd):/usr/app \
    -p 8000:8000 \
    --entrypoint "/bin/bash" \
    $DOCKER_NAME
