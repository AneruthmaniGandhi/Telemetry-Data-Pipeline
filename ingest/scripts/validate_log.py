from datetime import datetime
from typing import Optional, Dict, Union
from pydantic import BaseModel, Field, validator
import json
import sys

class SensorReadings(BaseModel):
    temperature: float = Field(..., ge=0, le=100)  # Temperature in Celsius
    vibration: float = Field(..., ge=0, le=1)      # Vibration in mm/s
    power_consumption: float = Field(..., ge=0)    # Power in kW

class TelemetryLog(BaseModel):
    timestamp: datetime
    equipment_id: str = Field(..., pattern=r'^(CNC|ROBOT)-\d{3}$')
    status: str = Field(..., pattern=r'^(operational|error)$')
    error_code: Optional[str] = Field(None, pattern=r'^E\d{3}$')
    sensor_readings: SensorReadings
    location: str = Field(..., pattern=r'^Factory-[A-C]$')
    maintenance_due: bool

    @validator('error_code')
    def validate_error_code(cls, v, values):
        if values.get('status') == 'error' and v is None:
            raise ValueError('error_code must be provided when status is error')
        if values.get('status') == 'operational' and v is not None:
            raise ValueError('error_code must be null when status is operational')
        return v

def validate_log_line(line: str) -> Union[TelemetryLog, str]:
    """
    Validate a single JSON log line against the schema.
    Returns the validated TelemetryLog object if valid, or error message if invalid.
    """
    try:
        data = json.loads(line)
        return TelemetryLog(**data)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"
    except Exception as e:
        return f"Validation error: {str(e)}"

def main():
    """
    Read log file from stdin and validate each line.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        result = validate_log_line(line)
        if isinstance(result, str):
            print(f"❌ {result}")
            sys.exit(1)
        else:
            print(f"✅ Valid log entry for {result.equipment_id}")

if __name__ == "__main__":
    main() 