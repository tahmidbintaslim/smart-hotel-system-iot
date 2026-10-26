#!/bin/bash

# Deployment script for Smart Hotel Management System

# Exit on any error
set -e

# Constants
DOCKER_COMPOSE_FILE="docker-compose.yml"
NETWORK_NAME="smart-hotel-network" # fixed by `name:` in docker-compose.yml

# Azure OpenAI settings for the chat page come from the shell or from a .env
# file in the repo root (copy .env.example)
if [ -f .env ]; then
    set -a
    # shellcheck source=/dev/null
    . ./.env
    set +a
fi
export AZURE_OPENAI_KEY="${AZURE_OPENAI_KEY:-}"
export AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-}"
export AZURE_ASSISTANT_ID="${AZURE_ASSISTANT_ID:-}"
export BACKEND_API_URL="http://iot-simulation:8000" # Updated to match service name in docker-compose

# Function to check Docker and Docker Compose installations
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Prefer the Compose plugin (`docker compose`), fall back to the standalone tool
compose() {
    if docker compose version &> /dev/null; then
        docker compose "$@"
    elif command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        echo "Error: Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# The chat page needs Azure OpenAI; the sensor API and the agents run without it
check_env_vars() {
    if [ -z "$AZURE_OPENAI_KEY" ] || [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_ASSISTANT_ID" ]; then
        echo "Warning: AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT or AZURE_ASSISTANT_ID is not set."
        echo "         The stack starts, but the chat page cannot answer."
    fi
}

# Build Docker images
build_images() {
    echo "Building Docker images..."
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        echo "Error: $DOCKER_COMPOSE_FILE not found. Ensure the file exists in the current directory."
        exit 1
    fi
    compose -f "$DOCKER_COMPOSE_FILE" build
}

# Start Docker services
start_services() {
    echo "Starting services..."
    compose -f "$DOCKER_COMPOSE_FILE" up -d
}

# Stop and remove Docker services
stop_services() {
    echo "Stopping and removing services..."
    compose -f "$DOCKER_COMPOSE_FILE" down
}

# Check Docker network status
check_network() {
    echo "Checking Docker network..."
    if ! docker network inspect "$NETWORK_NAME" &> /dev/null; then
        echo "Error: Docker network '$NETWORK_NAME' not found. Ensure the services are deployed correctly."
        exit 1
    fi
    echo "Docker network '$NETWORK_NAME' is configured."
}

# Main deployment function
deploy() {
    echo "Deploying Smart Hotel Management System..."
    check_docker
    check_env_vars
    build_images
    start_services
    check_network
    echo "Deployment completed successfully!"
}

# CLI argument parsing
case "$1" in
    start)
        deploy
        ;;
    stop)
        stop_services
        echo "Services stopped successfully!"
        ;;
    restart)
        stop_services
        deploy
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac

exit 0
