import streamlit as st
import duckdb
import pandas as pd

# Function to load data into DuckDB and return a connection
# We can use Streamlit's caching to avoid reloading data on every interaction.
@st.cache_resource # Caches the DuckDB connection resource
def get_duckdb_connection():
    con = duckdb.connect(database=':memory:', read_only=False)
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    con.execute(f"SET s3_endpoint='localhost:9000';")
    con.execute(f"SET s3_access_key_id='minioadmin';")
    con.execute(f"SET s3_secret_access_key='minioadmin';")
    con.execute("SET s3_use_ssl=false;")
    con.execute("SET s3_url_style='path';")
    return con

@st.cache_data # Caches the data loading step
def load_telemetry_data(_conn):
    s3_path = "s3://processed-logs/telemetry.parquet/*.parquet*"
    try:
        # Using a temporary table name for loading to avoid conflicts if function is called multiple times by cache
        _conn.execute(f"CREATE OR REPLACE TABLE telemetry_data_temp AS SELECT * FROM read_parquet(['{s3_path}']);")
        df = _conn.execute("SELECT * FROM telemetry_data_temp").fetchdf()
        _conn.execute("DROP TABLE telemetry_data_temp;") # Clean up temp table
        return df
    except Exception as e:
        st.error(f"Error loading data from MinIO: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

def main():
    st.set_page_config(layout="wide")
    st.title("Telemetry Data Pipeline Dashboard")

    conn = get_duckdb_connection()
    telemetry_df = load_telemetry_data(conn)

    if not telemetry_df.empty:
        st.header("Raw Data Overview")
        st.dataframe(telemetry_df.head())

        st.header("Top 5 Failure Types")
        # Filter out NULL or empty error codes before grouping
        error_counts = telemetry_df[telemetry_df['error_code'].notna() & (telemetry_df['error_code'] != '')] \
                        .groupby('error_code').size().reset_index(name='count') \
                        .sort_values(by='count', ascending=False).head(5)

        if not error_counts.empty:
            st.bar_chart(error_counts.set_index('error_code')['count'])
            st.dataframe(error_counts)
        else:
            st.write("No failure types found or all error codes are NULL/empty.")
        
        # You can add more visualizations here based on other tasks or insights
        # For example, equipment status, sensor readings trends, etc.

    else:
        st.warning("Could not load telemetry data. Please check MinIO connection and data availability.")

if __name__ == "__main__":
    main() 