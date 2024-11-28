import csv
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd

app = FastAPI()

# Simulate data from IoT devices
app.include_router(router, prefix="/api", tags=["API"])

# Define data models
class LifeBeingSensor(BaseModel):
    presence_state: str
    sensitivity: int
    online_status: str

class IAQSensor(BaseModel):
    noise: float
    co2: float
    pm25: float
    humidity: float
    temperature: float
    illuminance: float
    online_status: str
    device_status: str

# Read mock data from CSV
def read_csv_data(file_path: str):
    import pandas as pd
    import os

    # Get the absolute path to the CSV file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, "../../", file_path)

    # Load data into a DataFrame
    data = pd.read_csv(full_path)

    # Strip whitespace and newline characters from column names
    data.columns = data.columns.str.strip()

    # Use pivot_table to handle duplicates by aggregating with the 'last' value
    pivoted_data = data.pivot_table(
        index="device_id",
        columns="datapoint",
        values="value",
        aggfunc="last"  # Use the most recent value in case of duplicates
    )

    # Separate data for Life Being Sensor and IAQ Sensor
    life_being_data = pivoted_data.loc["life_being"].to_dict() if "life_being" in pivoted_data.index else {}
    iaq_data = pivoted_data.loc["iaq"].to_dict() if "iaq" in pivoted_data.index else {}

    # Convert data into list of objects
    life_being_data_list = [
        LifeBeingSensor(
            presence_state=life_being_data.get("presence_state", "unknown").strip('"'),  # Remove quotes
            sensitivity=int(float(life_being_data.get("sensitivity", 0))),
            online_status=life_being_data.get("online_status", "offline").strip('"'),  # Remove quotes
        )
    ]

    iaq_data_list = [
        IAQSensor(
            noise=float(iaq_data.get("noise", 30.0)),  # Default: 30.0 dB
            co2=float(iaq_data.get("co2", 400.0)),     # Default: 400.0 ppm
            pm25=float(iaq_data.get("pm25", 10.0)),   # Default: 10.0 µg/m³
            humidity=float(iaq_data.get("humidity", 50.0)),  # Default: 50.0%
            temperature=float(iaq_data.get("temperature", 22.0)),  # Default: 22.0°C
            illuminance=float(iaq_data.get("illuminance", 100.0)),  # Default: 100.0 lx
            online_status=iaq_data.get("online_status", "online").strip('"'),  # Default: "online"
            device_status=iaq_data.get("device_status", "active").strip('"'),  # Default: "active"
        )
    ]

    return life_being_data_list, iaq_data_list


# Routes
@app.get("/")
def root():
    return {"message": "Root endpoint works!"}

@app.get("/life-being/", response_model=List[LifeBeingSensor])
def get_life_being_data():
    # Read and return life being data
    life_being_data, _ = read_csv_data("data/room_iot_data.csv")
    return life_being_data

@app.get("/iaq/", response_model=List[IAQSensor])
def get_iaq_data():
    # Read and return IAQ data
    _, iaq_data = read_csv_data("data/room_iot_data.csv")
    return iaq_data
