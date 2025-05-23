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
    
    # Check if MinIO container is already running
    if docker ps | grep -q minio; then
        print_success "MinIO is already running"
        return 0
    fi
    
    # Create MinIO data directory if it doesn't exist
    mkdir -p minio-data
    
    # Start MinIO container
    docker run -d \
        --name minio \
        -p 9000:9000 \
        -p 9001:9001 \
        -v "$(pwd)/minio-data:/data" \
        -e "MINIO_ROOT_USER=minioadmin" \
        -e "MINIO_ROOT_PASSWORD=minioadmin" \
        minio/minio server /data --console-address ":9001"
    
    # Wait a moment for MinIO to start
    sleep 5
    
    # Create the required buckets
    print_step "Creating MinIO buckets..."
    if command -v python3 &> /dev/null; then
        # Install boto3 if needed
        pip3 install boto3 > /dev/null 2>&1 || true
        python3 create_buckets.py
    else
        print_error "Python3 not found - please create buckets manually"
    fi
    
    print_success "MinIO started on http://localhost:9000"
    print_success "MinIO Console on http://localhost:9001"
    print_warning "Default credentials: minioadmin/minioadmin"
    
    # Connect to Airflow network if it exists
    if docker network ls | grep -q airflow_default; then
        docker network connect airflow_default minio 2>/dev/null || true
        print_success "Connected MinIO to Airflow network"
    fi
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
    
    # Install ingestion dependencies if needed
    if [ -f "ingest/requirements.txt" ]; then
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        pip install -r ingest/requirements.txt > /dev/null 2>&1
    fi
    
    cd ingest/scripts
    if [ -f "fetch_logs_from_factories.py" ]; then
        python3 fetch_logs_from_factories.py
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
            run_ingestion
            setup_airflow
            print_success "Full setup completed!"
            echo ""
            echo "🌐 Access points:"
            echo "   - MinIO: http://localhost:9000 (minioadmin/minioadmin)"
            echo "   - Airflow: http://localhost:8080 (airflow/airflow)"
            echo ""
            echo "📊 Your pipeline is ready to run!"
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
            # Stop MinIO container
            if docker ps | grep -q minio; then
                docker stop minio && docker rm minio
                print_success "MinIO stopped"
            fi
            # Stop Airflow services
            cd pipeline_orchestration/airflow && docker-compose down
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