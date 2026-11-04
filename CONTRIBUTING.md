# Contributing

Thanks for your interest in the Smart Hotel System prototype. Issues and pull
requests are welcome.

## Before you start

- Read the [Status and roadmap](README.md#status-and-roadmap) section of the
  README. The known gaps listed there are good places to help, starting with a
  publisher that writes sensor readings to Kafka.
- For a larger change, open an issue first so the approach can be agreed on.
- Do not report security problems in a public issue; see
  [SECURITY.md](SECURITY.md).

## Development setup

You need Python 3.11, the version the Docker images and CI use.

```bash
git clone https://github.com/tahmidbintaslim/smart-hotel-system-iot.git
cd smart-hotel-system-iot
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The full Docker Compose stack is described in the README.

## Checks

CI runs these on every push to `main` and every pull request into `main`.
Run them before you push:

```bash
black --check .
flake8 .
pytest
shellcheck scripts/deploy.sh   # if you changed the script
```

The tests use fake Kafka and OpenAI clients, so they need no running
services. New behavior in the agents, the API or the chat page should come
with a test in `tests/`.

The packages under `backend/api`, `backend/cloud`, `backend/devices` and
`backend/kafka` are early drafts that black and flake8 skip. If you revive
one, remove it from the excludes in `pyproject.toml` and `.flake8`.

## Pull requests

- Keep each pull request to one change, and describe what and why.
- Use a short, imperative commit subject, for example
  `fix(agents): handle offline sensors`.
- Never commit `.env` or real keys; `.env.example` lists every variable.

## Questions

Open an issue, or email tahmidbintaslimrafi@gmail.com.

## License

By contributing, you agree that your contributions are licensed under the
GNU General Public License v3.0, the license of this project.
