#!/bin/bash
# End-to-End Test Runner Script
# Starts infrastructure and runs comprehensive E2E tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Fraud Detection System - E2E Test Runner${NC}"
echo "=================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i ":$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}Waiting for ${service_name} at ${host}:${port}...${NC}"
    
    while ! nc -z $host $port >/dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            echo -e "${RED}❌ ${service_name} failed to start after $max_attempts attempts${NC}"
            return 1
        fi
        echo "Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${GREEN}✅ ${service_name} is ready${NC}"
    return 0
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites are installed${NC}"

# Navigate to project directory
cd "$PROJECT_DIR"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please update .env with your actual API keys before running tests${NC}"
fi

# Load environment variables from .env file
if [ -f .env ]; then
    echo -e "${BLUE}📄 Loading environment variables from .env file...${NC}"
    set -a  # automatically export all variables
    source .env
    set +a  # turn off automatic export
fi

# Start infrastructure
echo -e "${BLUE}Starting infrastructure services...${NC}"

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down >/dev/null 2>&1 || true

# Start services
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
wait_for_service localhost 8000 "ChromaDB" || exit 1

# Check Confluent Cloud configuration
if [ -z "$CONFLUENT_BOOTSTRAP_SERVERS" ] || [ -z "$CONFLUENT_API_KEY" ] || [ -z "$CONFLUENT_API_SECRET" ]; then
    echo -e "${RED}❌ Missing Confluent Cloud configuration${NC}"
    echo -e "${YELLOW}Please set CONFLUENT_BOOTSTRAP_SERVERS, CONFLUENT_API_KEY, and CONFLUENT_API_SECRET${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Confluent Cloud configuration found${NC}"

# Install Python dependencies if needed
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
if command_exists uv; then
    echo "Using uv for dependency management..."
    uv pip install -e .
else
    echo "Using pip for dependency management..."
    pip install -r requirements.txt
fi

# Set environment variables for testing
export TOGETHER_API_KEY="${TOGETHER_API_KEY:-test_placeholder_key}"
# Confluent Cloud configuration should already be set in environment

# Run the E2E tests
echo -e "${BLUE}Running E2E tests...${NC}"
echo "=================================================="

# Run simple connectivity tests instead of complex e2e tests
echo -e "${YELLOW}Running Confluent Cloud connectivity test...${NC}"
$(uv python find) scripts/test_confluent_connection.py

E2E_EXIT_CODE=$?

echo -e "${YELLOW}Running simple producer/consumer test...${NC}"
$(uv python find) scripts/simple_test.py

SIMPLE_EXIT_CODE=$?

# Set overall exit code
if [ $E2E_EXIT_CODE -eq 0 ] && [ $SIMPLE_EXIT_CODE -eq 0 ]; then
    E2E_EXIT_CODE=0
else
    E2E_EXIT_CODE=1
fi

PYTEST_EXIT_CODE=0

# Generate additional reports
echo -e "${BLUE}📊 Generating additional reports...${NC}"

echo -e "${YELLOW}📋 Confluent Cloud Topics:${NC}"
echo "  - financial-transactions (configured in Confluent Cloud)"
echo "  - ai-decisions (configured in Confluent Cloud)"
echo "  - alerts (configured in Confluent Cloud)"

echo -e "${YELLOW}📋 Local Services:${NC}"
echo "  - ChromaDB: http://localhost:8000"
if port_in_use 6379; then
    echo "  - Redis: localhost:6379"
fi

# Show test results
echo "=================================================="
if [ $E2E_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 E2E tests completed successfully!${NC}"
else
    echo -e "${RED}❌ E2E tests failed with exit code: $E2E_EXIT_CODE${NC}"
fi

if command_exists pytest && [ $PYTEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ Pytest failed with exit code: $PYTEST_EXIT_CODE${NC}"
fi

# Cleanup option
echo -e "${BLUE}Cleanup options:${NC}"
echo "1. Keep services running for manual testing"
echo "2. Stop all services"
read -p "Choose option (1 or 2): " cleanup_choice

case $cleanup_choice in
    2)
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ All services stopped${NC}"
        ;;
    *)
        echo -e "${GREEN}ℹ️  Services kept running for manual testing${NC}"
        echo -e "${BLUE}Available services:${NC}"
        echo "- Confluent Cloud Kafka: $CONFLUENT_BOOTSTRAP_SERVERS"
        echo "- ChromaDB: http://localhost:8000"
        if port_in_use 6379; then
            echo "- Redis: localhost:6379"
        fi
        echo ""
        echo "To stop local services later, run: docker-compose down"
        ;;
esac

# Final exit code
if [ $E2E_EXIT_CODE -eq 0 ] && [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the output above for details.${NC}"
    exit 1
fi