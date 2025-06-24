#!/usr/bin/env bash
# Development helper script for video-services

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
function print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Install all dependencies (including dev and test)
function install() {
    print_header "Installing all dependencies"
    uv pip install -e ".[test,dev]"
    print_success "Dependencies installed"
}

# Run type checking with mypy
function typecheck() {
    print_header "Running type checks with mypy"
    mypy
}

# Run linting with ruff
function lint() {
    print_header "Running linter (ruff)"
    ruff check src/ tests/
}

# Run formatting with ruff
function format() {
    print_header "Formatting code with ruff"
    ruff format src/ tests/
    print_success "Code formatted"
}

# Run all tests
function test() {
    print_header "Running all tests"
    pytest
}

# Run unit tests only
function test_unit() {
    print_header "Running unit tests"
    pytest -m unit -v
}

# Run integration tests
function test_integration() {
    print_header "Running integration tests"
    pytest -m integration -v
}

# Run E2E tests
function test_e2e() {
    print_header "Running E2E tests"
    pytest -m e2e -v
}

# Run tests with coverage
function test_cov() {
    print_header "Running tests with coverage"
    pytest --cov=src --cov-report=term-missing --cov-report=html
    print_success "Coverage report generated in htmlcov/"
}

# Run all checks (type, lint, test)
function check() {
    print_header "Running all checks"
    
    echo "1. Type checking..."
    if typecheck; then
        print_success "Type check passed"
    else
        print_error "Type check failed"
        return 1
    fi
    
    echo -e "\n2. Linting..."
    if lint; then
        print_success "Linting passed"
    else
        print_error "Linting failed"
        return 1
    fi
    
    echo -e "\n3. Running tests..."
    if test; then
        print_success "All tests passed"
    else
        print_error "Tests failed"
        return 1
    fi
    
    print_success "All checks passed!"
}

# Run the development server
function serve() {
    print_header "Starting development server"
    python main.py
}

# Build Docker image
function docker_build() {
    print_header "Compiling requirements"
    uv pip compile pyproject.toml -o requirements.txt
    print_header "Building Docker image"
    docker build -t video-services .
    print_success "Docker image built"
}

# Run Docker container
function docker_run() {
    print_header "Running Docker container"
    docker run -p 8000:8000 video-services
}

# Clean up generated files
function clean() {
    print_header "Cleaning up generated files"
    
    # Remove Python cache files
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove test and coverage artifacts
    rm -rf .pytest_cache/
    rm -rf .mypy_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf coverage.xml
    
    # Remove build artifacts
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    
    print_success "Cleanup complete"
}

# Create sample test video
function create_test_video() {
    print_header "Creating sample test video"
    python tests/fixtures/create_sample_video.py
}

# Show help
function help() {
    echo "Video Services Development Helper"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install          Install all dependencies (including dev and test)"
    echo "  typecheck        Run type checking with mypy"
    echo "  lint             Run linting with ruff"
    echo "  format           Format code with ruff"
    echo "  test             Run all tests"
    echo "  test_unit        Run unit tests only"
    echo "  test_integration Run integration tests only"
    echo "  test_e2e         Run end-to-end tests"
    echo "  test_cov         Run tests with coverage report"
    echo "  check            Run all checks (type, lint, test)"
    echo "  serve            Start the development server"
    echo "  docker_build     Build Docker image"
    echo "  docker_run       Run Docker container"
    echo "  clean            Clean up generated files"
    echo "  create_test_video Create a sample test video"
    echo "  help             Show this help message"
}

# Main script logic
if [ $# -eq 0 ]; then
    help
    exit 0
fi

# Execute the requested function
case "$1" in
    (install|typecheck|lint|format|test|test_unit|test_integration|test_e2e|test_cov|check|serve|docker_build|docker_run|clean|create_test_video|help)
        "$1"
        ;;
    (*)
        print_error "Unknown command: $1"
        echo ""
        help
        exit 1
        ;;
esac