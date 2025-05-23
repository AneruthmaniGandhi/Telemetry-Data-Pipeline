#!/bin/bash

# 🏗️ Telemetry Pipeline Setup Script
# This script helps set up and run the telemetry data pipeline components

set -e

echo "🚀 Telemetry Pipeline Setup"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to setup MinIO
setup_minio() {
    print_step "Setting up MinIO (S3-compatible storage)..."
    cd storage/minio
    if [ -f docker-compose.yml ]; then
        docker-compose up -d
        print_success "MinIO started on http://localhost:9000"
        print_warning "Default credentials: minioadmin/minioadmin"
    else
        print_error "MinIO docker-compose.yml not found"
    fi
    cd ../..
}

# Function to setup Airflow
setup_airflow() {
    print_step "Setting up Apache Airflow..."
    cd pipeline_orchestration/airflow
    
    # Check if Dockerfile exists
    if [ ! -f Dockerfile ]; then
        print_error "Airflow Dockerfile not found"
        cd ../..
        return 1
    fi
    
    # Build and start Airflow
    docker-compose up airflow-init
    docker-compose up -d
    
    print_success "Airflow started on http://localhost:8080"
    print_warning "Default credentials: airflow/airflow"
    cd ../..
}

# Function to install Python dependencies
setup_python_env() {
    print_step "Setting up Python environment..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install processing requirements
    if [ -f "processing/requirements.txt" ]; then
        pip install -r processing/requirements.txt
        print_success "Installed processing dependencies"
    fi
    
    print_success "Python environment ready"
}

# Function to run ingestion
run_ingestion() {
    print_step "Running data ingestion..."
    cd ingest/scripts
    if [ -f "fetch_logs_from_factories.py" ]; then
        python fetch_logs_from_factories.py
        print_success "Data ingestion completed"
    else
        print_warning "Ingestion script not found - you may need to create sample data"
    fi
    cd ../..
}

# Main setup function
main() {
    echo ""
    echo "Select setup option:"
    echo "1) Full setup (MinIO + Airflow + Python env)"
    echo "2) Setup MinIO only"
    echo "3) Setup Airflow only"
    echo "4) Setup Python environment only"
    echo "5) Run ingestion"
    echo "6) Stop all services"
    echo ""
    read -p "Enter your choice [1-6]: " choice
    
    check_docker
    
    case $choice in
        1)
            setup_minio
            setup_python_env
            setup_airflow
            print_success "Full setup completed!"
            echo ""
            echo "🌐 Access points:"
            echo "   - MinIO: http://localhost:9000 (minioadmin/minioadmin)"
            echo "   - Airflow: http://localhost:8080 (airflow/airflow)"
            ;;
        2)
            setup_minio
            ;;
        3)
            setup_airflow
            ;;
        4)
            setup_python_env
            ;;
        5)
            run_ingestion
            ;;
        6)
            print_step "Stopping all services..."
            cd storage/minio && docker-compose down
            cd ../../pipeline_orchestration/airflow && docker-compose down
            cd ../..
            print_success "All services stopped"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Run main function
main 