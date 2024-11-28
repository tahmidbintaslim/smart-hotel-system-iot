import csv
import random
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI(title="IoT Device Simulation")

# Data models for sensors
class LifeBeingSensor(BaseModel):
    room_id: str
    presence_state: bool
    sensitivity: float
    online_status: bool
    timestamp: datetime

class IAQSensor(BaseModel):
    room_id: str
    noise: float
    co2: float
    pm25: float
    humidity: float
    temperature: float
    illuminance: float
    online_status: bool
    device_status: str
    timestamp: datetime

# Simulated data storage
life_being_data: Dict[str, List[LifeBeingSensor]] = {}
iaq_data: Dict[str, List[IAQSensor]] = {}

def load_csv_data(filepath: str) -> List[Dict]:
    """Load data from CSV file"""
    with open(filepath, 'r') as csvfile:
        return list(csv.DictReader(csvfile))

def generate_mock_life_being_data(room_id: str) -> LifeBeingSensor:
    """Generate mock Life Being sensor data"""
    return LifeBeingSensor(
        room_id=room_id,
        presence_state=random.choice([True, False]),
        sensitivity=round(random.uniform(0.1, 1.0), 2),
        online_status=random.choice([True, False]),
        timestamp=datetime.now()
    )

def generate_mock_iaq_data(room_id: str) -> IAQSensor:
    """Generate mock IAQ sensor data"""
    return IAQSensor(
        room_id=room_id,
        noise=round(random.uniform(30, 70), 1),
        co2=round(random.uniform(400, 2000), 1),
        pm25=round(random.uniform(0, 50), 1),
        humidity=round(random.uniform(30, 70), 1),
        temperature=round(random.uniform(20, 30), 1),
        illuminance=round(random.uniform(0, 1000), 1),
        online_status=random.choice([True, False]),
        device_status=random.choice(['normal', 'warning', 'critical']),
        timestamp=datetime.now()
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Backend IoT Device Simulation API"}

# Sensor data endpoints
@app.get("/life-being")
async def get_all_life_being_data():
    return {"message": "Not implemented yet"}

# IAQ sensor data endpoints
@app.get("/iaq")
async def get_all_iaq_data():
    return {"message": "Not implemented yet"}


@app.on_event("startup")
def preload_mock_data():
    for room_id in range(100, 110):  # Example room IDs from 100 to 109
        room_id_str = str(room_id)
        life_being_data[room_id_str] = [generate_mock_life_being_data(room_id_str)]
        iaq_data[room_id_str] = [generate_mock_iaq_data(room_id_str)]



# Room Life Being sensor data endpoints
@app.get("/life-being/{room_id}", response_model=LifeBeingSensor)
async def get_life_being_data(room_id: str):
    """Endpoint to get Life Being sensor data"""
    # Generate or retrieve mock data
    sensor_data = generate_mock_life_being_data(room_id)

    # Store data
    if room_id not in life_being_data:
        life_being_data[room_id] = []
    life_being_data[room_id].append(sensor_data)

    # Debug log
    print(f"Life Being Data for {room_id}: {life_being_data[room_id]}")

    return sensor_data


# Room IAQ sensor data endpoints
@app.get("/iaq/{room_id}", response_model=IAQSensor)
async def get_iaq_data(room_id: str):
    """Endpoint to get IAQ sensor data"""
    # Generate or retrieve mock data
    sensor_data = generate_mock_iaq_data(room_id)

    # Store data
    if room_id not in iaq_data:
        iaq_data[room_id] = []
    iaq_data[room_id].append(sensor_data)

    # Debug log
    print(f"IAQ Data for {room_id}: {iaq_data[room_id]}")

    return sensor_data


# Combined sensor data endpoints for a room
@app.get("/rooms/{room_id}/data", response_model=Dict[str, BaseModel])
async def get_room_data(room_id: str):
    """Endpoint to get combined sensor data for a room"""
    # Retrieve the latest stored data for life being sensor
    life_being = (
        life_being_data.get(room_id, [{}])[-1]
    )

    # Retrieve the latest stored data for IAQ sensor
    iaq = (
        iaq_data.get(room_id, [{}])[-1]
    )

    if not life_being or not iaq:
        raise HTTPException(status_code=404, detail="Room data not found")

    return {
        "life_being": life_being,
        "iaq": iaq
    }


@app.post("/rooms/{room_id}/control")
async def control_room_devices(room_id: str, command: Dict[str, str]):
    """Endpoint to send control commands to room devices"""
    # In a real implementation, this would interact with actual IoT devices
    return {
        "room_id": room_id,
        "command": command,
        "status": "processed"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)