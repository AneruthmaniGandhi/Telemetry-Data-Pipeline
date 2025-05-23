from __future__ import annotations

import pendulum
import logging
import sys
import os
import importlib.util

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

# Add project root to Python path to allow importing project modules
PROJECT_ROOT = '/opt/airflow/project_code' # Changed to the new mount point
INGEST_SCRIPT_DIR = os.path.join(PROJECT_ROOT, 'ingest', 'scripts')
PROCESSING_SCRIPT_DIR = os.path.join(PROJECT_ROOT, 'processing', 'spark_jobs')
WAREHOUSE_SCRIPT_DIR = os.path.join(PROJECT_ROOT, 'warehouse')

# Ensure script directories are in the Python path for Airflow worker
# While importlib.util.spec_from_file_location uses absolute paths,
# keeping these can be helpful if the scripts themselves have relative imports.
if INGEST_SCRIPT_DIR not in sys.path:
    sys.path.append(INGEST_SCRIPT_DIR)
if PROCESSING_SCRIPT_DIR not in sys.path:
    sys.path.append(PROCESSING_SCRIPT_DIR)
if WAREHOUSE_SCRIPT_DIR not in sys.path:
    sys.path.append(WAREHOUSE_SCRIPT_DIR)

# --- Helper function to load and run a script's main() ---
def _run_script_main(script_full_path: str, module_name: str):
    logging.info(f"Attempting to load module '{module_name}' from '{script_full_path}'")
    spec = importlib.util.spec_from_file_location(module_name, script_full_path)
    if spec is None:
        logging.error(f"Could not create module spec for {module_name} at {script_full_path}")
        raise ImportError(f"Cannot find module spec for {module_name} at {script_full_path}")
    
    module_to_run = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        logging.error(f"Module spec for {module_name} has no loader.")
        raise ImportError(f"Module spec for {module_name} has no loader.")
        
    sys.modules[module_name] = module_to_run # Add to sys.modules before execution
    spec.loader.exec_module(module_to_run)
    
    if hasattr(module_to_run, 'main') and callable(module_to_run.main):
        logging.info(f"Successfully imported and found main() in {module_name}. Running main()...")
        module_to_run.main()
        logging.info(f"Successfully ran main() from {module_name}")
    else:
        logging.error(f"Script {script_full_path} does not have a callable main() function.")
        raise AttributeError(f"Script {script_full_path} does not have a callable main() function.")

# --- Task Functions ---
def run_ingestion_task(**kwargs):
    logging.info(f"--- Running Ingestion Task ---")
    script_name = "fetch_logs_from_factories.py"
    script_path = os.path.join(INGEST_SCRIPT_DIR, script_name)
    _run_script_main(script_path, "fetch_logs_from_factories")

def run_spark_etl_task(**kwargs):
    logging.info(f"--- Running Spark ETL Task ---")
    # Set environment variables for this task execution
    os.environ['JAVA_HOME'] = "/usr/lib/jvm/java-17-openjdk-arm64"
    original_path = os.environ.get('PATH', '')
    # Ensure /usr/bin (for ps) and Java bin are at the start of the PATH
    # to avoid potential conflicts with other paths.
    os.environ['PATH'] = f"/usr/bin:/usr/lib/jvm/java-17-openjdk-arm64/bin:{original_path}"
    
    logging.info(f"Set JAVA_HOME to: {os.environ['JAVA_HOME']}")
    logging.info(f"Set PATH to: {os.environ['PATH']}")

    script_name = "etl_pipeline.py" # Assuming this is your main Spark ETL script
    script_path = os.path.join(PROCESSING_SCRIPT_DIR, script_name)
    _run_script_main(script_path, "etl_pipeline")

def run_load_to_duckdb_task(**kwargs):
    logging.info(f"--- Running Load to DuckDB Task ---")
    script_name = "load_to_duckdb.py"
    script_path = os.path.join(WAREHOUSE_SCRIPT_DIR, script_name)
    _run_script_main(script_path, "load_to_duckdb")

# --- DAG Definition ---
with DAG(
    dag_id="telemetry_pipeline_dag",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"), # Adjust start date as needed
    catchup=False,
    schedule="@daily", # Define your desired schedule, or None for manual triggers
    tags=["telemetry", "etl"],
    doc_md="""
    ### Telemetry Data Pipeline DAG
    Orchestrates the end-to-end telemetry data pipeline:
    1. Ingests raw logs and uploads to MinIO.
    2. Runs a Spark ETL job to process raw logs into Parquet format.
    3. Loads the processed Parquet data into a DuckDB data warehouse.
    """
) as dag:
    ingest_task = PythonOperator(
        task_id="upload_raw_logs_to_minio",
        python_callable=run_ingestion_task,
    )

    spark_etl_task = PythonOperator(
        task_id="run_spark_etl",
        python_callable=run_spark_etl_task,
    )

    duckdb_load_task = PythonOperator(
        task_id="load_to_duckdb",
        python_callable=run_load_to_duckdb_task,
    )

    # Define task dependencies
    ingest_task >> spark_etl_task >> duckdb_load_task 