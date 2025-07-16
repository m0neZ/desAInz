# Mocking External Services

Tests often need to run without real Kafka or Redis instances. Use lightweight mocks to simulate these dependencies.

## Kafka

`tests/test_kafka_utils.py` replaces the actual Kafka producer and consumer with dummy classes using `monkeypatch`.

```python
from backend.shared.kafka.utils import KafkaProducerWrapper

class DummyProducer:
    def __init__(self, *args, **kwargs):
        self.sent = {}

    def send(self, topic: str, value: dict) -> None:
        self.sent[topic] = value

    def flush(self) -> None:  # pragma: no cover
        pass

def test_producer(monkeypatch):
    monkeypatch.setattr('backend.shared.kafka.utils.KafkaProducer', DummyProducer)
    producer = KafkaProducerWrapper('kafka:9092', registry)
    producer.produce('signals', {'id': '1'})
    assert producer._producer.sent['signals'] == {'id': '1'}
```

## Redis

`backend/scoring-engine/tests/test_cache.py` uses `fakeredis` to emulate Redis in memory.

```python
import fakeredis
from scoring_engine.app import redis_client

redis_client.connection_pool.connection_class = fakeredis.FakeConnection
```

With this setup, Redis operations run against an in-memory store without requiring a real server.
