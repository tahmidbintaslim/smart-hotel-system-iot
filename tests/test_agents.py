import asyncio
import json
from datetime import datetime

import pytest

from backend.agents import data_logger, occupancy_detector
from fakes import FakeConsumer, FakeMessage, FakeProducer

AC_ECO_COMMAND = {"device": "ac", "action": "set_temperature", "value": 26.5}


def presence(room_id, present, sensitivity=0.9, online=True):
    return {
        "room_id": room_id,
        "presence_state": present,
        "sensitivity": sensitivity,
        "online_status": online,
        "timestamp": "2026-10-26T00:28:15.021913",
    }


@pytest.fixture
def detector(monkeypatch):
    monkeypatch.setattr(occupancy_detector, "Consumer", FakeConsumer)
    monkeypatch.setattr(occupancy_detector, "Producer", FakeProducer)
    return occupancy_detector.OccupancyDetectorAgent(
        kafka_broker="kafka:9092", iot_api_url="http://iot-simulation:8000"
    )


@pytest.mark.parametrize(
    "reading, occupied",
    [
        (presence("101", True), True),
        (presence("101", False), False),
        (presence("101", True, sensitivity=0.5), False),
        (presence("101", True, online=False), False),
        ({"room_id": "101"}, False),
    ],
)
def test_occupancy_rule(detector, reading, occupied):
    assert bool(detector.analyze_occupancy(reading)) is occupied


def test_detector_subscribes_to_life_being(detector):
    assert detector.consumer.topics == ["life-being"]


def run_detector_until_idle(detector, readings):
    """Feed readings to the agent loop and stop it once the queue is empty"""
    detector.consumer.messages = [FakeMessage("life-being", r) for r in readings]
    sent = []

    async def record_http_command(room_id, command):
        sent.append((room_id, command))

    detector.send_control_command = record_http_command

    def poll(timeout):
        if detector.consumer.messages:
            return detector.consumer.messages.pop(0)
        raise asyncio.CancelledError  # BaseException: leaves the loop

    detector.consumer.poll = poll
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(detector.run())
    return sent


def test_room_becoming_empty_sends_eco_set_point(detector):
    sent = run_detector_until_idle(
        detector, [presence("101", True), presence("101", False)]
    )
    assert sent == [("101", AC_ECO_COMMAND)]
    topic, key, value = detector.producer.produced[0]
    assert (topic, key) == ("room-control", b"101")
    assert json.loads(value) == AC_ECO_COMMAND


def test_no_command_while_occupancy_is_unchanged(detector):
    sent = run_detector_until_idle(
        detector,
        [presence("101", True), presence("101", True), presence("102", False)],
    )
    # Room 102 starts as unoccupied, so a first "empty" reading is no change
    assert sent == []
    assert detector.producer.produced == []
    assert detector.room_occupancy == {"101": True, "102": False}


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2026-10-26T00:28:15.021913", datetime(2026, 10, 26, 0, 28, 15, 21913)),
        ("2026-10-26T00:30:00", datetime(2026, 10, 26, 0, 30)),
        (datetime(2026, 10, 26), datetime(2026, 10, 26)),
        (None, None),
    ],
)
def test_parse_timestamp(value, expected):
    assert data_logger.parse_timestamp(value) == expected


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, entry):
        self.added.append(entry)

    async def commit(self):
        self.commits += 1


@pytest.fixture
def logger_agent(monkeypatch):
    monkeypatch.setattr(data_logger, "Consumer", FakeConsumer)
    # The engine connects lazily, so no database is needed here
    return data_logger.DataLoggerAgent(
        kafka_broker="kafka:9092",
        database_url="postgresql+asyncpg://user:password@localhost:5432/iotdb",
    )


def test_logger_subscribes_to_both_topics(logger_agent):
    assert logger_agent.consumer.topics == ["life-being", "iaq"]


def test_logger_maps_life_being_reading(logger_agent):
    session = FakeSession()
    asyncio.run(logger_agent.log_life_being_data(session, presence("101", True)))
    (entry,) = session.added
    assert isinstance(entry, data_logger.LifeBeingSensorLog)
    assert entry.room_id == "101"
    assert entry.presence_state is True
    assert entry.timestamp == datetime(2026, 10, 26, 0, 28, 15, 21913)
    assert session.commits == 1


def test_logger_maps_iaq_reading(logger_agent):
    reading = {
        "room_id": "102",
        "noise": 39.3,
        "co2": 1883.9,
        "pm25": 10.3,
        "humidity": 60.4,
        "temperature": 27.0,
        "illuminance": 347.4,
        "online_status": False,
        "device_status": "critical",
        "timestamp": "2026-10-26T00:28:15.037704",
    }
    session = FakeSession()
    asyncio.run(logger_agent.log_iaq_data(session, reading))
    (entry,) = session.added
    assert isinstance(entry, data_logger.IAQSensorLog)
    assert entry.co2 == 1883.9
    assert entry.device_status == "critical"
    assert entry.timestamp == datetime(2026, 10, 26, 0, 28, 15, 37704)
