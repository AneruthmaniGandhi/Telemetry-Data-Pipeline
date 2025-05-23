# Telemetry Data Pipeline

A production-ready telemetry data pipeline built with Apache Spark, MinIO, DuckDB, and Airflow for processing equipment monitoring data from multiple factories.

## 🏗️ Architecture

```
Raw Logs → MinIO → Spark ETL → Parquet → DuckDB → Analytics
    ↓         ↓         ↓         ↓         ↓
  JSON    S3 Bucket  Processing  Optimized  Warehouse
```

## 🚀 Quick Start

1. **Start the pipeline infrastructure:**
   ```bash
   ./setup.sh
   ```

2. **Access the services:**
   - **Airflow UI**: http://localhost:8080 (airflow/airflow)
   - **MinIO Console**: http://localhost:9000 (minioadmin/minioadmin)

3. **Run the pipeline:**
   - Go to Airflow UI → DAGs → `telemetry_pipeline_dag`
   - Click "Trigger DAG" to run the complete pipeline

## 📊 Pipeline Components

### 1. Data Ingestion (`ingest/`)
- **`scripts/fetch_logs_from_factories.py`**: Simulates collecting telemetry logs from multiple factory locations
- Uploads JSON logs to MinIO S3-compatible storage

### 2. ETL Processing (`processing/`)
- **`spark_jobs/etl_pipeline.py`**: Apache Spark job for data transformation
- Reads JSONL files from MinIO using boto3
- Processes 168+ telemetry records with sensor data
- Outputs optimized Parquet format

### 3. Data Warehouse (`warehouse/`)
- **`load_to_duckdb.py`**: Loads processed Parquet data into DuckDB
- **`duckdb/schema.sql`**: Database schema definition
- Provides analytics-ready data warehouse

### 4. Orchestration (`pipeline_orchestration/`)
- **Airflow DAG**: `telemetry_pipeline_dag.py`
- Docker Compose setup for scalable execution
- Automated task dependencies and error handling

## 📈 Data Flow

**Input Data:**
- Equipment IDs: CNC-001, CNC-002, ROBOT-001, etc.
- Sensor readings: temperature, vibration, power consumption
- Status tracking: operational vs error states
- Location data: Factory-A, Factory-B, Factory-C
- Error codes: E101, E202, etc.

**Processing Results:**
- **624 total records** processed
- **66.7% operational** equipment (416 records)
- **33.3% error states** (208 records)
- Optimized Parquet storage for fast analytics

## 🛠️ Technology Stack

- **Storage**: MinIO (S3-compatible object storage)
- **Processing**: Apache Spark 4.0 + Python 3.12
- **Analytics**: DuckDB with S3 integration
- **Orchestration**: Apache Airflow 2.10
- **Containerization**: Docker Compose

## 📁 Project Structure

```
├── README.md                          # This file
├── setup.sh                           # Infrastructure setup script
├── create_buckets.py                  # MinIO bucket creation
├── pipeline_orchestration/
│   └── airflow/
│       ├── docker-compose.yaml        # Airflow services
│       └── dags/
│           └── telemetry_pipeline_dag.py  # Main DAG
├── ingest/
│   └── scripts/
│       └── fetch_logs_from_factories.py   # Data ingestion
├── processing/
│   └── spark_jobs/
│       └── etl_pipeline.py            # Spark ETL job
├── warehouse/
│   ├── load_to_duckdb.py             # DuckDB loader
│   └── duckdb/
│       └── schema.sql                # Database schema
└── viz/
    └── streamlit_app/
        └── dashboard.py               # Visualization dashboard
```

## 🔧 Development

**Prerequisites:**
- Docker & Docker Compose
- 8GB+ RAM recommended

**Key Scripts:**
- `./setup.sh` - Start all services
- `create_buckets.py` - Initialize MinIO buckets
- `test_pipeline.py` - Manual pipeline testing

## 📊 Analytics

The pipeline provides analytics-ready data in DuckDB format:

```sql
-- Equipment status distribution
SELECT status, COUNT(*) FROM diagnostics GROUP BY status;

-- Sensor readings analysis
SELECT equipment_id, AVG(sensor_readings.temperature) 
FROM diagnostics WHERE status = 'operational' 
GROUP BY equipment_id;
```

## 🎯 Use Cases

- **Equipment Monitoring**: Real-time status tracking
- **Predictive Maintenance**: Sensor data analysis
- **Factory Analytics**: Multi-location performance
- **Error Tracking**: Failure pattern identification

---

**Built with ❤️ for industrial IoT analytics** 