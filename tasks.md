# 🧩 MVP Build Plan — Telemetry Data Pipeline (Step-by-Step)

## 📦 1. Project Setup

### `1.1` Initialize project structure
- **Start**: Create `telemetry-pipeline/` root folder and subfolders.
- **End**: All expected folders exist (ingest, processing, storage, etc.).

### `1.2` Initialize git repo and README
- **Start**: Inside root folder.
- **End**: `git init`, `.gitignore`, and `README.md` created.

## 🛂 2. Ingestion (Python + Simulated Logs)

### `2.1` Create sample telemetry log file
- **Start**: Ingest `logs/sample_log.jsonl`.
- **End**: File contains 10+ fake diagnostic logs (JSON lines format).

### `2.2` Write schema validation function
- **Start**: Use `pydantic` or `jsonschema` in `ingest/scripts/validate_log.py`.
- **End**: Function raises error if JSON line doesn't match expected schema.

### `2.3` Create ingestion script to move logs to MinIO
- **Start**: `fetch_logs_from_factories.py` reads logs and uploads to MinIO bucket via `boto3`.
- **End**: Script uploads validated logs to `minio://raw-logs/`.

## 🗃️ 3. Storage (MinIO)

### `3.1` Set up MinIO with Docker Compose
- **Start**: Write `storage/minio/docker-compose.yml`.
- **End**: `localhost:9000` MinIO UI works with test bucket `raw-logs`.

### `3.2` Verify Python upload + list files in MinIO
- **Start**: Modify ingestion script to list uploaded logs.
- **End**: Can view + confirm files inside MinIO programmatically.

## 🔄 4. ETL (Spark)

### `4.1` Setup PySpark project structure
- **Start**: `processing/spark_jobs/etl_pipeline.py` with `main()` defined.
- **End**: PySpark job loads JSON from MinIO using `s3a://` path.

### `4.2` Convert JSON to Parquet and write back to MinIO
- **Start**: Load raw log → write as Parquet to `s3a://processed-logs/`.
- **End**: Parquet file appears in processed folder in MinIO.

## 🧠 5. Data Warehouse (DuckDB)

### `5.1` Load Parquet from MinIO to DuckDB
- **Start**: Use `duckdb.connect()` and `read_parquet()` in script or notebook.
- **End**: Can query basic stats from log (e.g., count, failure codes).

### `5.2` Create DuckDB schema + table definition
- **Start**: Write `warehouse/duckdb/schema.sql` for structured telemetry data.
- **End**: `CREATE TABLE diagnostics (...)` works and inserts rows from Parquet.

## 📊 6. Visualization (Streamlit)

### `6.1` Setup Streamlit app + layout
- **Start**: `viz/streamlit_app/dashboard.py`.
- **End**: Runs and displays "Hello Telemetry".

### `6.2` Visualize basic metrics from DuckDB
- **Start**: Add DuckDB connection + query for counts, types.
- **End**: Streamlit dashboard shows top 5 failure types from logs.

## ⚙️ 7. Orchestration (Airflow)

### `7.1` Set up Airflow with Docker Compose
- **Start**: `pipeline_orchestration/airflow/docker-compose.yml`.
- **End**: UI runs at `localhost:8080` with default user.

### `7.2` Create DAG for end-to-end ingestion → processing
- **Start**: `dags/telemetry_pipeline_dag.py` with 3 tasks:
  - Upload raw logs
  - Run Spark ETL
  - Load to DuckDB
- **End**: DAG succeeds, all steps completed sequentially.

## 📈 8. Monitoring (Prometheus + Grafana)

### `8.1` Configure Prometheus to scrape custom script metrics
- **Start**: Write script that logs counters using Prometheus client.
- **End**: Metrics appear at `localhost:9090`.

### `8.2` Create Grafana dashboard with log stats
- **Start**: `monitoring/grafana/docker-compose.yml`, link to Prometheus.
- **End**: Dashboard shows ETL counts, file sizes, or last ingestion time.

## 🧪 9. Testing & Final Integration

### `9.1` End-to-end test with new log file
- **Start**: Drop new JSONL file into ingest.
- **End**: File gets ingested, transformed, stored, and visible in Streamlit.

### `9.2` Write minimal test cases for ingestion + ETL
- **Start**: Add `tests/` folder.
- **End**: Run `pytest` on schema validation + ETL output format.
