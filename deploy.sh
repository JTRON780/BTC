#!/bin/bash
# BTC Sentiment Analysis - Docker Deployment Script
# Usage: ./deploy.sh [build|start|stop|restart|logs|status]

set -e

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="btc-sentiment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found!"
        if [ -f .env.example ]; then
            print_msg "Copying .env.example to .env..."
            cp .env.example .env
            print_warning "Please update .env with your configuration before running services."
        else
            print_error ".env.example not found! Please create .env file manually."
            exit 1
        fi
    else
        print_msg "✓ .env file found"
    fi
}

# Build Docker images
build() {
    print_msg "Building Docker images..."
    docker build -t ${PROJECT_NAME}-api --build-arg MODE=api .
    docker build -t ${PROJECT_NAME}-app --build-arg MODE=app .
    print_msg "✓ Build completed successfully"
}

# Start services
start() {
    print_msg "Starting services..."
    check_env
    docker compose -f ${COMPOSE_FILE} up -d
    print_msg "✓ Services started"
    print_msg "API: http://localhost:8000"
    print_msg "Dashboard: http://localhost:8501"
    print_msg "API Docs: http://localhost:8000/docs"
}

# Stop services
stop() {
    print_msg "Stopping services..."
    docker compose -f ${COMPOSE_FILE} down
    print_msg "✓ Services stopped"
}

# Restart services
restart() {
    print_msg "Restarting services..."
    stop
    start
}

# View logs
logs() {
    print_msg "Viewing logs (Ctrl+C to exit)..."
    docker compose -f ${COMPOSE_FILE} logs -f
}

# Check status
status() {
    print_msg "Service Status:"
    docker compose -f ${COMPOSE_FILE} ps
    echo ""
    print_msg "Health Checks:"
    
    # Check API health
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        print_msg "✓ API is healthy"
    else
        print_error "✗ API is not responding"
    fi
    
    # Check Dashboard
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        print_msg "✓ Dashboard is accessible"
    else
        print_error "✗ Dashboard is not responding"
    fi
}

# Clean everything (including volumes)
clean() {
    print_warning "This will remove all containers, images, and volumes!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_msg "Cleaning up..."
        docker compose -f ${COMPOSE_FILE} down -v
        docker rmi ${PROJECT_NAME}-api ${PROJECT_NAME}-app 2>/dev/null || true
        print_msg "✓ Cleanup completed"
    else
        print_msg "Cleanup cancelled"
    fi
}

# Show help
help() {
    echo "BTC Sentiment Analysis - Docker Deployment"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker images"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs        View service logs"
    echo "  status      Check service status"
    echo "  clean       Remove all containers, images, and volumes"
    echo "  help        Show this help message"
    echo ""
}

# Main command handler
case "$1" in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    help|--help|-h|"")
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
