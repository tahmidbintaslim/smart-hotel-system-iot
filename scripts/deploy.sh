#!/bin/bash

# Deployment script for Smart Hotel Management System

# Exit on any error
set -e

# Constants
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Set Azure OpenAI and Backend environment variables
export AZURE_OPENAI_KEY="4jcVWz6srd4Y7INprd7cpXGvodoPprnYd3cO3vC920sRWrXSCbvKJQQJ99AKACYeBjFXJ3w3AABACOGBqv1"
export AZURE_OPENAI_ENDPOINT="https://gpt-candidate-test.openai.azure.com"
export AZURE_ASSISTANT_ID="asst_7y4J1Znzk3Agv6zvFTCEhj1Q"
export BACKEND_API_URL="http://iot-simulation:8000" # Updated to match service name in docker-compose

# Function to check Docker and Docker Compose installations
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "Error: Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Check for required environment variables
check_env_vars() {
    if [ -z "$AZURE_OPENAI_KEY" ] || [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_ASSISTANT_ID" ] || [ -z "$BACKEND_API_URL" ]; then
        echo "Error: Environment variables are not set. Please check AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_ASSISTANT_ID, and BACKEND_API_URL."
        exit 1
    fi
}

# Build Docker images
build_images() {
    echo "Building Docker images..."
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        echo "Error: $DOCKER_COMPOSE_FILE not found. Ensure the file exists in the current directory."
        exit 1
    fi
    docker-compose -f "$DOCKER_COMPOSE_FILE" build
}

# Start Docker services
start_services() {
    echo "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
}

# Stop and remove Docker services
stop_services() {
    echo "Stopping and removing services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
}

# Check Docker network status
check_network() {
    echo "Checking Docker network..."
    docker network inspect glowing-fortnight_default &> /dev/null
    if [ $? -ne 0 ]; then
        echo "Error: Docker network 'glowing-fortnight_default' not found. Ensure the services are deployed correctly."
        exit 1
    fi
    echo "Docker network 'glowing-fortnight_default' is configured."
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
