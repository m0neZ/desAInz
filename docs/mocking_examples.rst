Mocking Kafka and Redis
=======================

The test suite uses in-memory stand-ins to isolate services that normally depend on external
data stores.  ``pytest`` fixtures and ``monkeypatch`` provide convenient ways to replace
Kafka and Redis objects with lightweight substitutes.

Kafka
-----

``tests/test_kafka_utils.py`` demonstrates how to patch the Kafka producer so that
no broker is required.  The ``KafkaProducer`` class is replaced with ``DummyProducer``
which just records messages:

.. literalinclude:: ../tests/test_kafka_utils.py
   :language: python
   :lines: 6-31

Redis
-----

``backend/scoring-engine/tests/test_cache.py`` shows the use of ``fakeredis`` to
mock Redis while exercising caching logic:

.. literalinclude:: ../backend/scoring-engine/tests/test_cache.py
   :language: python
   :lines: 1-33
