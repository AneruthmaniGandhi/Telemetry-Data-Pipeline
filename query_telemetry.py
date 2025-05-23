from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, min, max, desc

def create_spark_session():
    return SparkSession.builder \
        .appName("Telemetry Analysis") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.1") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .getOrCreate()

def analyze_telemetry_data(spark):
    # Read the Parquet data
    df = spark.read.parquet("s3a://processed-logs/telemetry.parquet/")
    
    # Register the DataFrame as a temporary view for SQL queries
    df.createOrReplaceTempView("telemetry")
    
    print("\n=== Equipment Status Analysis ===")
    # Count of records by equipment status
    status_counts = df.groupBy("status").count().orderBy(desc("count"))
    print("\nEquipment Status Distribution:")
    status_counts.show()
    
    print("\n=== Error Code Analysis ===")
    # Count of records by error code
    error_counts = df.groupBy("error_code").count().orderBy(desc("count"))
    print("\nError Code Distribution:")
    error_counts.show()
    
    print("\n=== Sensor Readings Analysis ===")
    # Statistics for sensor readings
    sensor_stats = df.select(
        avg("sensor_readings.temperature").alias("avg_temperature"),
        min("sensor_readings.temperature").alias("min_temperature"),
        max("sensor_readings.temperature").alias("max_temperature"),
        avg("sensor_readings.vibration").alias("avg_vibration"),
        min("sensor_readings.vibration").alias("min_vibration"),
        max("sensor_readings.vibration").alias("max_vibration"),
        avg("sensor_readings.power_consumption").alias("avg_power_consumption"),
        min("sensor_readings.power_consumption").alias("min_power_consumption"),
        max("sensor_readings.power_consumption").alias("max_power_consumption")
    )
    print("\nSensor Reading Statistics:")
    sensor_stats.show()
    
    print("\n=== Equipment Performance Analysis ===")
    # Performance metrics by equipment ID
    performance_metrics = df.groupBy("equipment_id").agg(
        avg("sensor_readings.temperature").alias("avg_temperature"),
        avg("sensor_readings.vibration").alias("avg_vibration"),
        avg("sensor_readings.power_consumption").alias("avg_power_consumption"),
        count("*").alias("total_readings")
    ).orderBy("equipment_id")
    print("\nPerformance Metrics by Equipment:")
    performance_metrics.show()

def main():
    spark = create_spark_session()
    try:
        analyze_telemetry_data(spark)
    finally:
        spark.stop()

if __name__ == "__main__":
    main() 