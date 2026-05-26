from unittest.mock import patch, MagicMock


class ConsumerGroupIsolationTest:
    def test_ranking_consumer_uses_ranking_service_group(self):
        with patch("events.consumer_base.Consumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from events.consumer_base import make_consumer

            make_consumer("ranking-service", ["match.finished"])

        config = mock_cls.call_args[0][0]
        assert config["group.id"] == "ranking-service"

    def test_notification_consumer_uses_notification_service_group(self):
        with patch("events.consumer_base.Consumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from events.consumer_base import make_consumer

            make_consumer("notification-service", ["match.finished"])

        config = mock_cls.call_args[0][0]
        assert config["group.id"] == "notification-service"

    def test_log_consumer_uses_audit_log_service_group(self):
        with patch("events.consumer_base.Consumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from events.consumer_base import make_consumer

            make_consumer("audit-log-service", ["match.finished", "tournament.created"])

        config = mock_cls.call_args[0][0]
        assert config["group.id"] == "audit-log-service"

    def test_consumer_subscribes_to_given_topics(self):
        mock_consumer = MagicMock()
        with patch("events.consumer_base.Consumer", return_value=mock_consumer):
            from events.consumer_base import make_consumer

            make_consumer("ranking-service", ["match.finished"])

        mock_consumer.subscribe.assert_called_once_with(["match.finished"])

    def test_auto_commit_disabled(self):
        with patch("events.consumer_base.Consumer") as mock_cls:
            mock_cls.return_value = MagicMock()
            from events.consumer_base import make_consumer

            make_consumer("ranking-service", ["match.finished"])

        config = mock_cls.call_args[0][0]
        assert config["enable.auto.commit"] is False
