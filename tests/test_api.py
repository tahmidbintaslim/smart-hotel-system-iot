import pytest
from fastapi.testclient import TestClient

from backend.agents import data_fetcher
from backend.agents.data_fetcher import app

PRELOADED_ROOMS = [str(room) for room in range(100, 110)]


@pytest.fixture
def client():
    data_fetcher.life_being_data.clear()
    data_fetcher.iaq_data.clear()
    # Entering the context runs the startup handler that preloads rooms
    with TestClient(app) as test_client:
        yield test_client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend IoT Device Simulation API"}


def test_startup_preloads_rooms_100_to_109(client):
    assert sorted(data_fetcher.life_being_data) == PRELOADED_ROOMS
    assert sorted(data_fetcher.iaq_data) == PRELOADED_ROOMS


def test_life_being_reading(client):
    response = client.get("/life-being/105")
    assert response.status_code == 200
    reading = response.json()
    assert reading["room_id"] == "105"
    assert isinstance(reading["presence_state"], bool)
    assert 0.1 <= reading["sensitivity"] <= 1.0
    assert isinstance(reading["online_status"], bool)
    assert "timestamp" in reading


def test_iaq_reading(client):
    response = client.get("/iaq/105")
    assert response.status_code == 200
    reading = response.json()
    assert reading["room_id"] == "105"
    assert 30 <= reading["noise"] <= 70
    assert 400 <= reading["co2"] <= 2000
    assert 0 <= reading["pm25"] <= 50
    assert 30 <= reading["humidity"] <= 70
    assert 20 <= reading["temperature"] <= 30
    assert 0 <= reading["illuminance"] <= 1000
    assert reading["device_status"] in {"normal", "warning", "critical"}


def test_readings_are_stored_per_room(client):
    client.get("/life-being/105")
    client.get("/iaq/105")
    assert len(data_fetcher.life_being_data["105"]) == 2
    assert len(data_fetcher.iaq_data["105"]) == 2


def test_new_room_gets_readings_on_first_request(client):
    client.get("/life-being/200")
    client.get("/iaq/200")
    response = client.get("/rooms/200/data")
    assert response.status_code == 200
    assert response.json()["life_being"]["room_id"] == "200"


def test_room_data_returns_both_readings(client):
    response = client.get("/rooms/101/data")
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"life_being", "iaq"}
    assert data["life_being"]["room_id"] == "101"
    assert "presence_state" in data["life_being"]
    assert data["iaq"]["room_id"] == "101"
    assert "co2" in data["iaq"]


def test_room_data_returns_latest_reading(client):
    latest = client.get("/life-being/101").json()
    data = client.get("/rooms/101/data").json()
    assert data["life_being"] == latest


def test_room_data_unknown_room_is_404(client):
    response = client.get("/rooms/999/data")
    assert response.status_code == 404
    assert response.json() == {"detail": "Room data not found"}


def test_control_echoes_command(client):
    # The occupancy detector sends this command when a room becomes empty
    command = {"device": "ac", "action": "set_temperature", "value": 26.5}
    response = client.post("/rooms/101/control", json=command)
    assert response.status_code == 200
    assert response.json() == {
        "room_id": "101",
        "command": command,
        "status": "processed",
    }


@pytest.mark.parametrize("path", ["/life-being", "/iaq"])
def test_list_endpoints_are_not_implemented(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"message": "Not implemented yet"}
