#!/bin/bash
# Run sync in Docker container

# Build if needed
docker-compose build

# Run sync
docker-compose run --rm wefact-sync python3 sync.py "$@"
