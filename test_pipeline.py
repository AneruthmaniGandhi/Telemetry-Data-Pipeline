#!/usr/bin/env python3

"""
Test script to run the complete telemetry pipeline manually
This simulates what Airflow would do but runs locally for testing
"""

import os
import sys
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, description, cwd=None):
    """Run a command and log the results."""
    logger.info(f"🔄 {description}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        if result.returncode == 0:
            logger.info(f"✅ {description} - SUCCESS")
            if result.stdout:
                logger.info(f"Output: {result.stdout[:200]}...")
            return True
        else:
            logger.error(f"❌ {description} - FAILED")
            logger.error(f"Error: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ {description} - EXCEPTION: {str(e)}")
        return False

def main():
    """Run the complete pipeline test."""
    logger.info("🚀 Starting Complete Telemetry Pipeline Test")
    logger.info("=" * 60)
    
    # Step 1: Ingestion
    logger.info("📥 STEP 1: Data Ingestion")
    success = run_command(
        "python fetch_logs_from_factories.py",
        "Running data ingestion",
        cwd="ingest/scripts"
    )
    if not success:
        logger.error("Pipeline failed at ingestion step")
        return False
    
    time.sleep(2)  # Brief pause between steps
    
    # Step 2: Spark ETL
    logger.info("\n⚙️ STEP 2: Spark ETL Processing")
    success = run_command(
        "python etl_pipeline.py",
        "Running Spark ETL",
        cwd="processing/spark_jobs"
    )
    if not success:
        logger.error("Pipeline failed at ETL step")
        return False
    
    time.sleep(2)  # Brief pause between steps
    
    # Step 3: DuckDB Loading
    logger.info("\n🗄️ STEP 3: DuckDB Data Loading")
    success = run_command(
        "python load_to_duckdb.py",
        "Loading data to DuckDB",
        cwd="warehouse"
    )
    if not success:
        logger.error("Pipeline failed at DuckDB loading step")
        return False
    
    time.sleep(2)  # Brief pause between steps
    
    # Step 4: Data Quality Check
    logger.info("\n📊 STEP 4: Data Quality Analysis")
    success = run_command(
        "python query_duckdb.py",
        "Running data quality analysis",
        cwd="processing/warehouse"
    )
    if not success:
        logger.error("Pipeline failed at data quality step")
        return False
    
    # Final Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎉 PIPELINE TEST COMPLETED SUCCESSFULLY!")
    logger.info("=" * 60)
    logger.info("✅ All pipeline components are working correctly:")
    logger.info("   📥 Data Ingestion: Sample logs uploaded to MinIO")
    logger.info("   ⚙️ Spark ETL: JSON converted to Parquet format")
    logger.info("   🗄️ DuckDB Loading: Data loaded into analytics database")
    logger.info("   📊 Data Analysis: Quality checks and insights generated")
    logger.info("\n🌐 Access Points:")
    logger.info("   - MinIO UI: http://localhost:9000 (minioadmin/minioadmin)")
    logger.info("   - Airflow UI: http://localhost:8080 (airflow/airflow)")
    logger.info("\n🎯 Next Steps:")
    logger.info("   - Check the telemetry_pipeline_dag in Airflow UI")
    logger.info("   - Set up Streamlit dashboard for visualization")
    logger.info("   - Configure Prometheus/Grafana for monitoring")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 