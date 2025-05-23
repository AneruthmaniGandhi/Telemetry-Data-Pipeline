import duckdb
import os

def main():
    # Connect to an in-memory DuckDB database
    con = duckdb.connect(database=':memory:', read_only=False)

    # Install and load the httpfs extension for S3 access
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")

    # Configure S3 credentials and endpoint for MinIO
    con.execute(f"SET s3_endpoint='host.docker.internal:9000';")
    con.execute(f"SET s3_access_key_id='minioadmin';")
    con.execute(f"SET s3_secret_access_key='minioadmin';")
    con.execute("SET s3_use_ssl=false;") # Use http for MinIO
    con.execute("SET s3_url_style='path';")

    # Define the S3 path to the Parquet data
    s3_path = "s3://processed-logs/telemetry.parquet/*.parquet*" # Use s3:// and specific Parquet glob

    # Define path to schema file
    schema_file_path = os.path.join(os.path.dirname(__file__), "duckdb", "schema.sql")

    try:
        # Execute the schema.sql file to create the table
        print(f"Executing schema file: {schema_file_path}")
        with open(schema_file_path, 'r') as f:
            schema_sql = f.read()
        con.execute(schema_sql)
        print("Schema file executed successfully. 'diagnostics' table created (if not exists).")

        print(f"\nAttempting to read Parquet data from: {s3_path} and load into 'diagnostics' table")

        # Insert data from Parquet into the 'diagnostics' table
        con.execute(f"INSERT INTO diagnostics SELECT * FROM read_parquet(['{s3_path}']);")
        
        # Perform a basic query to verify
        result = con.execute("SELECT COUNT(*) FROM diagnostics;").fetchone()
        if result and result[0] is not None:
            print(f"Successfully loaded {result[0]} rows into DuckDB table 'diagnostics'.")
        else:
            print("Could not retrieve count from 'diagnostics'. Table might be empty or query failed.")

        # Example: Show schema of the diagnostics table
        print("\nSchema of 'diagnostics':")
        schema_info = con.execute("PRAGMA table_info('diagnostics');").fetchall()
        for col in schema_info:
            print(col)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    main() 