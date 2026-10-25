# Smart Hotel System (IoT prototype)

A prototype backend for smart hotel rooms. A FastAPI service simulates room
sensors, Docker Compose runs it next to Kafka, ZooKeeper and PostgreSQL, and a
Gradio chat page sends a room's data and a guest's question to an Azure OpenAI
assistant.

**Status:** prototype from November 2024; since then only dependency bumps. The
sensor API runs. The Kafka agents are written but not wired into the stack, and
the Docker images do not build with the current `requirements.txt`. See
[Known gaps](#known-gaps).

**License:** GNU General Public License v3.0 ([LICENSE](LICENSE)).

## What is in the repo

| Path | What it does |
| --- | --- |
| `backend/agents/data_fetcher.py` | FastAPI app on port 8000. Returns random readings for two simulated sensors per room: presence ("life being") and indoor air quality (noise, CO2, PM2.5, humidity, temperature, illuminance). Rooms 100 to 109 are preloaded at startup and readings are kept in memory. |
| `backend/agents/data_logger.py` | Kafka consumer for the `life-being` and `iaq` topics. Writes each reading to PostgreSQL with async SQLAlchemy. |
| `backend/agents/occupancy_detector.py` | Kafka consumer for `life-being`. A room counts as occupied when presence is true, sensitivity is above 0.5 and the sensor is online. When a room becomes empty it publishes an AC set point of 26.5 °C to the `room-control` topic and posts the same command to the API. |
| `frontend/chatbot.py` | Gradio chat page on port 7860. The first word of a message is the room ID. It fetches that room's data from the API and sends it with the question to an Azure OpenAI assistant (Assistants API). |
| `backend/devices/simulation.py`, `backend/api/routes.py`, `backend/kafka/producer.py`, `backend/cloud/azure_integration.py` | Early drafts. Nothing imports or runs them. |
| `docker-compose.yml`, `docker/` | Four containers built from `docker/Dockerfile.backend` (`iot-simulation`, `data-fetcher`, `data-logger`, `occupancy-detector`), PostgreSQL 13, ZooKeeper, Kafka and the chat page. |
| `scripts/deploy.sh` | Wraps `docker-compose` build, up and down. |
| `tests/` | Empty placeholder files. There are no tests yet. |

## Sensor API

| Request | Response |
| --- | --- |
| `GET /life-being/{room_id}` | A new random presence reading for the room, also stored in memory. |
| `GET /iaq/{room_id}` | A new random air quality reading for the room, also stored. |
| `GET /rooms/{room_id}/data` | Meant to return the latest stored reading of each sensor (see Known gaps). 404 for a room with no readings. |
| `POST /rooms/{room_id}/control` | Echoes the JSON command back with `"status": "processed"`. No device is controlled. |
| `GET /life-being`, `GET /iaq` | `"Not implemented yet"`. |

Interactive docs are at `/docs` while the API runs.

## Running it

### Sensor API only, without Docker

FastAPI 0.109 supports Python 3.8 and newer; these steps were checked with
Python 3.13. Run from the repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi==0.109.0 uvicorn==0.27.0
python -m backend.agents.data_fetcher
```

Then open http://localhost:8000/docs.

### Full stack with Docker Compose

This fails at the image build until the dependency conflict below is fixed.
The steps, for when it is:

1. Install Docker. `deploy.sh` calls the standalone `docker-compose` command.
2. Clone the repo and export your own Azure OpenAI settings for the chat page:

   ```bash
   git clone https://github.com/tahmidbintaslim/smart-hotel-system-iot.git
   cd smart-hotel-system-iot
   export AZURE_OPENAI_KEY=<your key>
   export AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
   export AZURE_ASSISTANT_ID=<your assistant id>
   ```

3. Start, stop or restart the stack (on Windows, prefix with `bash`):

   ```bash
   chmod +x ./scripts/deploy.sh   # Linux and macOS, once
   ./scripts/deploy.sh start
   ./scripts/deploy.sh stop
   ./scripts/deploy.sh restart
   ```

4. Open the chat page at http://localhost:7860 and type a room ID, then a
   question, for example `101 what is the temperature?`. The API docs are at
   http://localhost:8000/docs.

## Known gaps

- **The project images do not build.** `requirements.txt` pins `fastapi==0.109.0`, but
  `gradio==6.20.0` needs FastAPI 0.115.2 or newer, so `pip install` stops with a
  resolution error. The conflict began when Gradio moved to 5.5.0 (PR #1); the
  original pins, with Gradio 4.19.2, resolved.
- **The two Kafka agents never start.** `docker/Dockerfile.backend` ends with
  `CMD ["python", "-m", "backend.agents.data_fetcher"]`, and no service in
  `docker-compose.yml` sets `command:`. All four backend containers
  (`iot-simulation`, `data-fetcher`, `data-logger`, `occupancy-detector`)
  therefore run the sensor API. `data_fetcher.py` is the API itself, so there is
  no separate data fetcher agent; `data_logger.py` and `occupancy_detector.py`
  only run if started by hand.
- **Nothing feeds Kafka.** No code publishes readings to the `life-being` or
  `iaq` topics, so the logger and the occupancy detector have no input even
  when started by hand, and PostgreSQL stays empty.
- **`GET /rooms/{room_id}/data` returns empty objects**
  (`{"life_being": {}, "iaq": {}}`) because its response model is the bare
  Pydantic `BaseModel`. The chat page therefore sends the assistant no sensor
  values.
- **The chat handler mangles input and output.** It keeps only the text after
  the second word (`101 what is the temperature?` reaches the assistant as
  `is the temperature?`), returns the assistant message's content list instead
  of its text, and its status poll calls `asyncio.sleep` without `await`, so it
  does not pause between checks.
- **`deploy.sh start` can stop with an error after the containers are up.** Its
  last step looks for a Docker network named `glowing-fortnight_default`; the
  compose file defines `glowing-fortnight-network`.
- The draft modules import packages that are not in `requirements.txt`
  (`kafka-python`, `psycopg2`), and `backend/devices/simulation.py` uses an
  undefined `router` and reads a `data/room_iot_data.csv` that is not in the
  repo.
- The ZooKeeper and Kafka images use unpinned `latest` tags, so what they pull
  changes over time.
- PostgreSQL uses the placeholder login `user` / `password`, set in
  `docker-compose.yml` and `data_logger.py`. Local demo use only.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
