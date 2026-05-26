import json
import logging
from unittest.mock import MagicMock, patch

import pytest


class PublishEventTest:
    def test_produces_utf8_json_to_correct_topic(self):
        mock_producer = MagicMock()
        with patch("events.producer._get_producer", return_value=mock_producer):
            from events.producer import publish_event

            publish_event("match.finished", {"match_id": 1})

        mock_producer.produce.assert_called_once()
        call_kwargs = mock_producer.produce.call_args
        assert call_kwargs[0][0] == "match.finished"
        value = call_kwargs[1]["value"]
        assert json.loads(value.decode("utf-8")) == {"match_id": 1}

    def test_calls_flush_after_produce(self):
        mock_producer = MagicMock()
        with patch("events.producer._get_producer", return_value=mock_producer):
            from events.producer import publish_event

            publish_event("match.finished", {"match_id": 1})

        mock_producer.flush.assert_called_once()

    def test_silent_failure_when_broker_unreachable(self, caplog):
        mock_producer = MagicMock()
        mock_producer.produce.side_effect = Exception("broker unreachable")
        with patch("events.producer._get_producer", return_value=mock_producer):
            from events.producer import publish_event

            with caplog.at_level(logging.ERROR, logger="events.producer"):
                publish_event("match.finished", {"match_id": 99})

        assert any("match.finished" in r.message for r in caplog.records)
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_silent_failure_on_flush_error(self, caplog):
        mock_producer = MagicMock()
        mock_producer.flush.side_effect = Exception("flush failed")
        with patch("events.producer._get_producer", return_value=mock_producer):
            from events.producer import publish_event

            with caplog.at_level(logging.ERROR, logger="events.producer"):
                publish_event("match.finished", {"match_id": 5})

        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_reads_bootstrap_servers_from_env(self):
        with patch.dict("os.environ", {"KAFKA_BOOTSTRAP_SERVERS": "mybroker:9092"}):
            with patch("confluent_kafka.Producer") as mock_cls:
                mock_cls.return_value = MagicMock()
                from events import producer as prod_module
                import importlib
                importlib.reload(prod_module)
                prod_module._producer = None
                prod_module._get_producer()

            call_args = mock_cls.call_args[0][0]
            assert call_args["bootstrap.servers"] == "mybroker:9092"
