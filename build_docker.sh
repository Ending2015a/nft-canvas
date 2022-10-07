#!/bin/bash

DOCKER_BUILDKIT=1 docker build . \
  --build-arg INCUBATOR_VER=$(date +%Y%m%d-%H%M%S) \
  --file docker/usd.Dockerfile \
  -t ending2015a/usd

DOCKER_BUILDKIT=1 docker build . \
  --build-arg INCUBATOR_VER=$(date +%Y%m%d-%H%M%S) \
  --file docker/usd-from-gltf.Dockerfile \
  -t ending2015a/usd-from-gltf
