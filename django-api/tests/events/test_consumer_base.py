import time
from unittest.mock import MagicMock, call, patch

import pytest


class RetryHandlerTest:
    def test_successful_handler_not_retried(self):
        from events.consumer_base import handle_with_retry

        handler = MagicMock()
        msg = MagicMock()
        handle_with_retry(handler, msg, "match.finished")
        handler.assert_called_once_with(msg)

    def test_handler_retried_three_times_then_dlq(self):
        from events.consumer_base import handle_with_retry

        handler = MagicMock(side_effect=Exception("fail"))
        msg = MagicMock()

        mock_producer = MagicMock()
        with patch("events.consumer_base._get_dlq_producer", return_value=mock_producer):
            with patch("time.sleep"):
                handle_with_retry(handler, msg, "match.finished")

        assert handler.call_count == 4  # 1 initial + 3 retries

    def test_retry_uses_exponential_backoff(self):
        from events.consumer_base import handle_with_retry

        handler = MagicMock(side_effect=Exception("fail"))
        msg = MagicMock()
        sleep_calls = []

        def record_sleep(seconds):
            sleep_calls.append(seconds)

        mock_producer = MagicMock()
        with patch("events.consumer_base._get_dlq_producer", return_value=mock_producer):
            with patch("time.sleep", side_effect=record_sleep):
                handle_with_retry(handler, msg, "match.finished")

        assert sleep_calls == [1, 2, 4]

    def test_message_sent_to_dlq_on_exhaustion(self):
        from events.consumer_base import handle_with_retry

        handler = MagicMock(side_effect=Exception("fail"))
        msg = MagicMock()
        msg.value.return_value = b'{"match_id": 1}'

        mock_producer = MagicMock()
        with patch("events.consumer_base._get_dlq_producer", return_value=mock_producer):
            with patch("time.sleep"):
                handle_with_retry(handler, msg, "match.finished")

        mock_producer.produce.assert_called_once()
        call_kwargs = mock_producer.produce.call_args
        assert call_kwargs[0][0] == "match.finished.dlq"
        mock_producer.flush.assert_called_once()

    def test_recovers_on_second_attempt(self):
        from events.consumer_base import handle_with_retry

        handler = MagicMock(side_effect=[Exception("fail"), None])
        msg = MagicMock()

        mock_producer = MagicMock()
        with patch("events.consumer_base._get_dlq_producer", return_value=mock_producer):
            with patch("time.sleep"):
                handle_with_retry(handler, msg, "match.finished")

        assert handler.call_count == 2
        mock_producer.produce.assert_not_called()
