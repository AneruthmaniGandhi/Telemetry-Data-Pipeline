# 🏗️ Telemetry & Diagnostics Data Pipeline

An open-source pipeline for collecting, processing, and analyzing telemetry data from factory equipment.

## 📋 Overview

This pipeline:
1. Ingests diagnostic logs from factory equipment
2. Stores raw data in MinIO (S3-compatible storage)
3. Processes data with Apache Spark
4. Stores processed data in DuckDB
5. Visualizes insights with Streamlit
6. Orchestrates workflows with Airflow
7. Monitors performance with Prometheus/Grafana

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- Git

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd telemetry-pipeline
   ```

2. Start MinIO (S3-compatible storage):
   ```bash
   cd storage/minio
   docker-compose up -d
   ```

3. Install Python dependencies:
   ```bash
   cd processing
   pip install -r requirements.txt
   ```

4. Run the ingestion script:
   ```bash
   cd ingest/scripts
   python fetch_logs_from_factories.py
   ```

## 📁 Project Structure

```
telemetry-pipeline/
├── ingest/          # Log ingestion (NiFi, Python scripts)
├── storage/         # MinIO object storage
├── processing/      # Spark ETL jobs
├── warehouse/       # DuckDB analytical storage
├── monitoring/      # Prometheus + Grafana
├── viz/            # Streamlit dashboard
└── pipeline_orchestration/  # Airflow DAGs
```

## 🔧 Components

- **Ingestion**: Apache NiFi + Python scripts
- **Storage**: MinIO (S3-compatible)
- **Processing**: Apache Spark (PySpark)
- **Warehouse**: DuckDB
- **Orchestration**: Apache Airflow
- **Monitoring**: Prometheus + Grafana
- **Visualization**: Streamlit

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Development Guide](docs/development.md)
- [API Documentation](docs/api.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 