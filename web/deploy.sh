#!/bin/bash

# Ensure that the local branch is up to date with the remote branch
git pull

# Build the project
docker compose build

# Up all containers
docker compose up -d

# Clear docker cache
docker system prune -f