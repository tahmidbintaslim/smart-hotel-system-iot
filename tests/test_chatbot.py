from types import SimpleNamespace

import pytest

from frontend import chatbot


@pytest.mark.parametrize(
    "message, expected",
    [
        ("101 what is the temperature?", ("101", "what is the temperature?")),
        ("  104   is the room busy?  ", ("104", "is the room busy?")),
        ("hello", (chatbot.DEFAULT_ROOM_ID, "hello")),
    ],
)
def test_parse_message(message, expected):
    assert chatbot.parse_message(message) == expected


def text_block(value):
    return SimpleNamespace(type="text", text=SimpleNamespace(value=value))


def test_message_text_joins_text_blocks():
    message = SimpleNamespace(
        content=[
            text_block("It is 24 degrees."),
            SimpleNamespace(type="image_file"),
            text_block("CO2 is normal."),
        ]
    )
    assert chatbot.message_text(message) == "It is 24 degrees.\nCO2 is normal."


class FakeThreads:
    """Minimal stand-in for client.beta.threads with a run that queues once"""

    def __init__(self, reply):
        self.reply = reply
        self.sent = []
        self.statuses = ["queued", "in_progress", "completed"]
        self.messages = SimpleNamespace(create=self._create, list=self._list)
        self.runs = SimpleNamespace(create=self._run, retrieve=self._run)

    def create(self):
        return SimpleNamespace(id="thread_1")

    def _create(self, thread_id, role, content):
        self.sent.append(content)

    def _run(self, thread_id, assistant_id=None, run_id=None):
        return SimpleNamespace(id="run_1", status=self.statuses.pop(0))

    def _list(self, thread_id):
        reply = SimpleNamespace(role="assistant", content=[text_block(self.reply)])
        return SimpleNamespace(data=[reply])


@pytest.fixture
def assistant(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test-key")
    monkeypatch.setenv("AZURE_ASSISTANT_ID", "asst_test")
    sleeps = []
    monkeypatch.setattr(chatbot.time, "sleep", sleeps.append)
    bot = chatbot.HotelAssistant()
    bot.threads = FakeThreads("It is 24 degrees.")
    bot.client = SimpleNamespace(beta=SimpleNamespace(threads=bot.threads))
    bot.sleeps = sleeps
    return bot


def test_llm_response_returns_text_and_waits_between_polls(assistant):
    reply = assistant.generate_llm_response("what is the temperature?", {"iaq": {}})
    assert reply == "It is 24 degrees."
    assert assistant.sleeps == [1, 1]


def test_chat_sends_full_question_with_room_data(assistant, monkeypatch):
    requested = []

    async def fake_room_data(room_id):
        requested.append(room_id)
        return {"iaq": {"temperature": 24.0}}

    monkeypatch.setattr(assistant, "get_room_data", fake_room_data)
    reply = assistant.chat_interface("101 what is the temperature?", [])
    assert reply == "It is 24 degrees."
    assert requested == ["101"]
    assert assistant.threads.sent == [
        "Room data: {'iaq': {'temperature': 24.0}}\n"
        "User request: what is the temperature?"
    ]
