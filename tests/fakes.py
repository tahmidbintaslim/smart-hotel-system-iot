import json


class FakeMessage:
    """Stands in for a confluent_kafka.Message"""

    def __init__(self, topic, value):
        self._topic = topic
        self._value = json.dumps(value).encode("utf-8")

    def error(self):
        return None

    def topic(self):
        return self._topic

    def value(self):
        return self._value


class FakeConsumer:
    """Returns the queued messages, then None, like an idle topic"""

    def __init__(self, config=None):
        self.config = config
        self.topics = []
        self.messages = []

    def subscribe(self, topics):
        self.topics = topics

    def poll(self, timeout):
        return self.messages.pop(0) if self.messages else None


class FakeProducer:
    def __init__(self, config=None):
        self.config = config
        self.produced = []

    def produce(self, topic, key=None, value=None):
        self.produced.append((topic, key, value))

    def flush(self):
        pass
