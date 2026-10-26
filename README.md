# Smart Hotel System (IoT prototype)

[![CI](https://github.com/tahmidbintaslim/smart-hotel-system-iot/actions/workflows/ci.yml/badge.svg)](https://github.com/tahmidbintaslim/smart-hotel-system-iot/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)

A prototype backend for smart hotel rooms: a FastAPI service that simulates
room sensors, two Kafka consumer agents (one logs readings to PostgreSQL, one
sets the AC to an energy-saving temperature when a room empties), and a Gradio
chat page that answers guest questions about a room through an Azure OpenAI
assistant. Docker Compose runs the whole stack on one machine.

**Status:** prototype, written in November 2024 and repaired in October 2026.
It runs locally only; there is no hosted demo. Nothing publishes sensor
readings to Kafka yet, so the agents act only on readings you publish by hand
(see [Status and roadmap](#status-and-roadmap)).

![Swagger UI of the sensor API listing its seven endpoints](docs/images/api-docs.png)

![GET /rooms/101/data in Swagger UI returning the latest presence and air quality readings for room 101](docs/images/room-data-response.png)

## Features

- **Sensor API** (`backend/agents/data_fetcher.py`): returns random readings
  for two simulated sensors per room, presence ("life being") and indoor air
  quality (noise, CO2, PM2.5, humidity, temperature, illuminance). Rooms 100 to
  109 are preloaded at startup; readings are kept in memory.
- **Occupancy detector** (`backend/agents/occupancy_detector.py`): consumes the
  `life-being` topic. A room is occupied when presence is true, sensitivity is
  above 0.5 and the sensor is online. When a room becomes empty it publishes an
  AC set point of 26.5 °C to the `room-control` topic and posts the same command
  to the API.
- **Data logger** (`backend/agents/data_logger.py`): consumes the `life-being`
  and `iaq` topics and writes each reading to PostgreSQL with async SQLAlchemy.
  It creates its tables at startup.
- **Chat page** (`frontend/chatbot.py`): the first word of a message is the
  room ID, the rest is the question. It fetches that room's readings from the
  API and sends both to an Azure OpenAI assistant (Assistants API).
- **Docker Compose stack** with a `deploy.sh` wrapper, health-checked
  PostgreSQL, and host ports bound to `127.0.0.1`.
- **Tests and CI**: 33 pytest tests that need no Kafka, database or Azure, plus
  black, flake8, shellcheck and an image build on every push and pull request.

## Architecture

```mermaid
flowchart LR
    guest(["Guest browser"]) -->|"101 what is the temperature?"| chat["frontend<br/>Gradio chat page :7860"]
    chat -->|"GET /rooms/{id}/data"| api["iot-simulation<br/>FastAPI sensor API :8000"]
    chat -->|"readings + question"| azure[("Azure OpenAI<br/>Assistants API")]
    manual["No publisher yet:<br/>readings are published by hand"] -.->|"life-being, iaq"| kafka{{"Kafka + ZooKeeper<br/>Confluent 7.9.10"}}
    kafka -->|"life-being, iaq"| logger["data-logger agent"]
    logger -->|"INSERT"| pg[("PostgreSQL 13<br/>iotdb")]
    kafka -->|"life-being"| occ["occupancy-detector agent"]
    occ -->|"room-control"| kafka
    occ -->|"POST /rooms/{id}/control"| api
```

| Service | Image | Host port | Runs |
| --- | --- | --- | --- |
| `iot-simulation` | `docker/Dockerfile.backend` | 8000 | `python -m backend.agents.data_fetcher` |
| `data-logger` | `docker/Dockerfile.backend` | none | `python -m backend.agents.data_logger` |
| `occupancy-detector` | `docker/Dockerfile.backend` | none | `python -m backend.agents.occupancy_detector` |
| `frontend` | `docker/Dockerfile.frontend` | 7860 | `python -m frontend.chatbot` |
| `postgres` | `postgres:13` | 5432 (`POSTGRES_HOST_PORT`) | database `iotdb` |
| `kafka`, `zookeeper` | `confluentinc/cp-kafka`, `cp-zookeeper` 7.9.10 | 9092, 2181 | broker |

All host ports listen on `127.0.0.1` only.

### Sensor API

| Request | Response |
| --- | --- |
| `GET /life-being/{room_id}` | A new random presence reading for the room, also stored. |
| `GET /iaq/{room_id}` | A new random air quality reading for the room, also stored. |
| `GET /rooms/{room_id}/data` | The latest stored reading of each sensor. 404 for a room with no readings. |
| `POST /rooms/{room_id}/control` | Echoes the JSON command back with `"status": "processed"`. No device is controlled. |
| `GET /life-being`, `GET /iaq` | `"Not implemented yet"`. |

Interactive docs are at http://localhost:8000/docs while the API runs.

## Tech stack

Python 3.11, FastAPI 0.143 with Uvicorn and Pydantic 2, confluent-kafka,
SQLAlchemy 2 (async) with asyncpg, PostgreSQL 13, Apache Kafka and ZooKeeper
(Confluent Platform 7.9), Gradio 6, the OpenAI Python SDK against Azure
OpenAI, Docker Compose, pytest, black, flake8 and GitHub Actions.

## Getting started

### Prerequisites

- Python 3.11 (the Docker images and CI use 3.11)
- Git
- For the full stack: Docker with the Compose plugin (checked with Docker 29.9
  and Compose 5.6) or the standalone `docker-compose`, and about 5 GB of disk
  for the images
- For chat answers only: an Azure OpenAI resource with an Assistant

### Install and run the sensor API (no Docker)

```bash
git clone https://github.com/tahmidbintaslim/smart-hotel-system-iot.git
cd smart-hotel-system-iot
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m backend.agents.data_fetcher
```

Open http://localhost:8000/docs, or:

```bash
curl http://localhost:8000/rooms/101/data
```

### Test and lint

```bash
pytest                     # 33 tests, no services needed
black --check .
flake8 .
shellcheck scripts/deploy.sh   # if shellcheck is installed
```

CI runs the same commands, then `docker compose build`.

### Run the full stack (Docker Compose)

1. Create your `.env` from the template and fill in the Azure OpenAI values.
   Every variable is described in [.env.example](.env.example). Without them
   the stack still starts, but the chat page cannot answer.

   ```bash
   cp .env.example .env
   ```

2. Build and start (on Windows, run the script from Git Bash or WSL):

   ```bash
   ./scripts/deploy.sh start      # build, start, check the network
   ./scripts/deploy.sh restart
   ./scripts/deploy.sh stop
   ```

   `docker compose up -d --build` and `docker compose down` work too.

3. Open the chat page at http://localhost:7860 and type a room ID, then a
   question, for example `101 what is the temperature?`. The API docs are at
   http://localhost:8000/docs.

4. Exercise the Kafka agents by publishing a reading from the API by hand:

   ```bash
   curl -s localhost:8000/life-being/102 | docker compose exec -T kafka \
     kafka-console-producer --bootstrap-server kafka:9092 --topic life-being
   curl -s localhost:8000/iaq/102 | docker compose exec -T kafka \
     kafka-console-producer --bootstrap-server kafka:9092 --topic iaq

   docker compose exec postgres psql -U user -d iotdb \
     -c "select * from life_being_sensor_logs" -c "select * from iaq_sensor_logs"
   docker compose logs occupancy-detector
   ```

   The first messages can take up to a minute to appear while the consumers
   join their groups. Kafka advertises itself as `kafka:9092`, so clients on
   the host cannot use the published port 9092; run them inside the network as
   above.

### Configuration

| Variable | Used by | Default |
| --- | --- | --- |
| `AZURE_OPENAI_KEY` | chat page | none |
| `AZURE_OPENAI_ENDPOINT` | chat page | none |
| `AZURE_ASSISTANT_ID` | chat page | none |
| `POSTGRES_HOST_PORT` | `docker-compose.yml` | `5432` |
| `BACKEND_API_URL` | chat page | `http://localhost:8000` (Compose sets `http://iot-simulation:8000`) |
| `KAFKA_BROKER` | both agents | `kafka:9092` |
| `DATABASE_URL` | data logger | `postgresql+asyncpg://user:password@postgres:5432/iotdb` |
| `IOT_API_URL` | occupancy detector | `http://iot-simulation:8000` |

Keep real keys in `.env` or your shell. `.env` is ignored by git and by the
Docker build context.

## Deployment

Not deployed anywhere. The project runs on a single machine with Docker
Compose; `scripts/deploy.sh` wraps `docker compose build`, `up -d` and `down`
and checks that the `smart-hotel-network` network exists. PostgreSQL uses the
placeholder login `user` / `password` and the chat page has no login, so keep
the stack on localhost.

## Project structure

```text
backend/agents/
  data_fetcher.py        FastAPI sensor API (the iot-simulation service)
  data_logger.py         Kafka -> PostgreSQL agent
  occupancy_detector.py  Kafka -> AC set point agent
backend/api, backend/cloud, backend/devices, backend/kafka
                         early drafts; nothing imports or runs them
frontend/chatbot.py      Gradio chat page
docker/                  Dockerfiles for the backend and the chat page
docker-compose.yml       the full stack
scripts/deploy.sh        start / stop / restart wrapper
tests/                   pytest suite with fake Kafka and OpenAI clients
.github/                 CI workflow and Dependabot
```

## Status and roadmap

Checked on 2026-10-26 with `docker compose up`: all seven containers start,
each agent runs its own module, and readings published by hand reach
PostgreSQL and trigger the AC command (logged by the occupancy detector and
answered by the API). The chat page fetches the room's readings and sends them
to Azure OpenAI (checked against a dummy endpoint); its answers were not tested
against a live Azure OpenAI assistant in this pass.

Known gaps:

- **Nothing publishes readings to Kafka.** A small publisher that polls the
  API and writes to `life-being` and `iaq` would close the loop.
- The four packages under `backend/api`, `backend/cloud`, `backend/devices`
  and `backend/kafka` are drafts. They import packages that are not in
  `requirements.txt` (`kafka-python`, `psycopg2`), and
  `backend/devices/simulation.py` uses an undefined `router` and a CSV file
  that is not in the repo. Lint and formatting checks skip them.
- The API keeps every reading in memory with no limit, and `GET /life-being`
  and `GET /iaq` are not implemented.
- The data logger runs SQLAlchemy with `echo=True`, so it logs every SQL
  statement.
- The API uses FastAPI's deprecated `on_event("startup")` hook, which logs a
  deprecation warning.

## Contributing

Issues and pull requests are welcome. Before you push, run `black .`,
`flake8 .` and `pytest`; CI runs the same checks and builds the Docker images.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
