CREATE TABLE IF NOT EXISTS diagnostics (
    timestamp TIMESTAMP,
    equipment_id VARCHAR,
    status VARCHAR,
    error_code VARCHAR,
    sensor_readings STRUCT(temperature DOUBLE, vibration DOUBLE, power_consumption DOUBLE),
    location VARCHAR,
    maintenance_due BOOLEAN
); 