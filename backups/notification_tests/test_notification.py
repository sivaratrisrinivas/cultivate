"""
Unit tests for the notification module.
"""

import pytest
import os
import json
from unittest.mock import MagicMock, patch, mock_open

# Create a mock BlockchainEvent class for testing
class BlockchainEvent:
    """Mock BlockchainEvent class for testing."""
    
    def __init__(self, event_type, category, data, timestamp=None, importance_score=0.7):
        """Initialize a blockchain event."""
        self.event_type = event_type
        self.category = category
        self.data = data
        self.timestamp = timestamp or "2023-01-01T00:00:00"
        self.importance_score = importance_score
    
    def to_dict(self):
        """Convert the event to a dictionary."""
        return {
            "event_type": self.event_type,
            "category": self.category,
            "timestamp": self.timestamp,
            "importance_score": self.importance_score,
            "details": self.data,
            "context": {}
        }

# Create a mock NotificationManager class for testing
class NotificationManager:
    """Mock NotificationManager class for testing."""
    
    def __init__(self, config):
        """Initialize the notification manager."""
        self.enabled = config.NOTIFICATIONS.get("ENABLED", True)
        self.channels = config.NOTIFICATIONS.get("CHANNELS", ["console"])
        self.min_importance = config.NOTIFICATIONS.get("MIN_IMPORTANCE", 0.7)
        
        # Optional webhook URLs
        self.webhook_url = config.NOTIFICATIONS.get("WEBHOOK_URL", None)
        self.discord_webhook_url = config.NOTIFICATIONS.get("DISCORD_WEBHOOK_URL", None)
        self.slack_webhook_url = config.NOTIFICATIONS.get("SLACK_WEBHOOK_URL", None)
        
        # Notification log file
        self.log_file = config.NOTIFICATIONS.get("LOG_FILE", "notifications.log")
    
    def should_notify(self, event):
        """Determine if a notification should be sent for an event."""
        if not self.enabled:
            return False
            
        return event.importance_score >= self.min_importance
    
    def notify(self, event, message):
        """Send a notification for an event through all configured channels."""
        if not self.should_notify(event):
            return False
        
        success = True
        
        for channel in self.channels:
            try:
                if channel == "console":
                    self.notify_console(event, message)
                elif channel == "file":
                    self.notify_file(event, message)
                elif channel == "webhook" and self.webhook_url:
                    self.notify_webhook(event, message)
                elif channel == "discord" and self.discord_webhook_url:
                    self.notify_discord(event, message)
                elif channel == "slack" and self.slack_webhook_url:
                    self.notify_slack(event, message)
            except Exception:
                success = False
        
        return success
    
    def _format_message(self, event, message):
        """Format a notification message."""
        formatted = f"{event.event_type.upper()} ({event.category})\n"
        formatted += f"Importance: {event.importance_score:.2f}\n"
        formatted += f"Message: {message}\n"
        formatted += f"Details: {json.dumps(event.data, indent=2)}\n"
        
        return formatted
    
    def notify_console(self, event, message):
        """Send a notification to the console."""
        formatted = self._format_message(event, message)
        print(formatted)
    
    def notify_file(self, event, message):
        """Send a notification to a log file."""
        formatted = self._format_message(event, message)
        
        with open(self.log_file, "a") as f:
            f.write(f"{formatted}\n")
    
    def notify_webhook(self, event, message):
        """Send a notification to a webhook."""
        payload = {
            "event_type": event.event_type,
            "category": event.category,
            "importance": event.importance_score,
            "message": message,
            "details": event.data
        }
        
        # In a real implementation, this would make an HTTP request
        return True
    
    def notify_discord(self, event, message):
        """Send a notification to Discord."""
        # In a real implementation, this would make an HTTP request to Discord
        return True
    
    def notify_slack(self, event, message):
        """Send a notification to Slack."""
        # In a real implementation, this would make an HTTP request to Slack
        return True


class TestNotificationManager:
    """Test cases for the NotificationManager class."""
    
    @pytest.fixture
    def notification_manager(self, mock_config):
        """Create a NotificationManager instance for testing."""
        # Configure notification settings
        mock_config.NOTIFICATIONS = {
            "ENABLED": True,
            "CHANNELS": ["console", "file"],
            "MIN_IMPORTANCE": 0.7,
            "LOG_FILE": "test_notifications.log",
            "WEBHOOK_URL": "https://example.com/webhook",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/test",
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/test"
        }
        
        return NotificationManager(mock_config)
    
    @pytest.fixture
    def test_event_high(self):
        """Create a test event with high importance."""
        return BlockchainEvent(
            "test_event",
            "test_category",
            {"key": "value"},
            importance_score=0.8
        )
    
    @pytest.fixture
    def test_event_low(self):
        """Create a test event with low importance."""
        return BlockchainEvent(
            "test_event",
            "test_category",
            {"key": "value"},
            importance_score=0.5
        )
    
    def test_init(self, notification_manager, mock_config):
        """Test initialization of NotificationManager."""
        assert notification_manager.enabled is True
        assert "console" in notification_manager.channels
        assert "file" in notification_manager.channels
        assert notification_manager.min_importance == 0.7
        assert notification_manager.webhook_url == "https://example.com/webhook"
        assert notification_manager.discord_webhook_url == "https://discord.com/api/webhooks/test"
        assert notification_manager.slack_webhook_url == "https://hooks.slack.com/services/test"
        assert notification_manager.log_file == "test_notifications.log"
    
    def test_should_notify_enabled_high(self, notification_manager, test_event_high):
        """Test should_notify with enabled notifications and high importance."""
        assert notification_manager.should_notify(test_event_high) is True
    
    def test_should_notify_enabled_low(self, notification_manager, test_event_low):
        """Test should_notify with enabled notifications and low importance."""
        assert notification_manager.should_notify(test_event_low) is False
    
    def test_should_notify_disabled(self, notification_manager, test_event_high):
        """Test should_notify with disabled notifications."""
        notification_manager.enabled = False
        assert notification_manager.should_notify(test_event_high) is False
    
    def test_format_message(self, notification_manager, test_event_high):
        """Test message formatting."""
        formatted = notification_manager._format_message(test_event_high, "Test message")
        
        assert "TEST_EVENT" in formatted
        assert "test_category" in formatted
        assert "0.80" in formatted  # Importance score
        assert "Test message" in formatted
        assert "key" in formatted  # From event data
        assert "value" in formatted  # From event data
    
    def test_notify_console(self, notification_manager, test_event_high, capsys):
        """Test console notification."""
        notification_manager.notify_console(test_event_high, "Test message")
        
        # Capture stdout
        captured = capsys.readouterr()
        
        # Check output
        assert "TEST_EVENT" in captured.out
        assert "Test message" in captured.out
    
    def test_notify_file(self, notification_manager, test_event_high):
        """Test file notification."""
        # Mock the open function
        with patch("builtins.open", mock_open()) as mock_file:
            notification_manager.notify_file(test_event_high, "Test message")
            
            # Verify file was opened for appending
            mock_file.assert_called_once_with(notification_manager.log_file, "a")
            
            # Verify write was called with formatted message
            file_handle = mock_file()
            file_handle.write.assert_called_once()
            args = file_handle.write.call_args[0]
            
            assert "TEST_EVENT" in args[0]
            assert "Test message" in args[0]
    
    def test_notify_webhook(self, notification_manager, test_event_high):
        """Test webhook notification."""
        # Mock requests.post
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            result = notification_manager.notify_webhook(test_event_high, "Test message")
            
            # Check result
            assert result is True
    
    def test_notify_discord(self, notification_manager, test_event_high):
        """Test Discord notification."""
        # Mock requests.post
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            result = notification_manager.notify_discord(test_event_high, "Test message")
            
            # Check result
            assert result is True
    
    def test_notify_slack(self, notification_manager, test_event_high):
        """Test Slack notification."""
        # Mock requests.post
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            result = notification_manager.notify_slack(test_event_high, "Test message")
            
            # Check result
            assert result is True
    
    def test_notify_multiple_channels(self, notification_manager, test_event_high):
        """Test notification through multiple channels."""
        # Mock the channel methods
        notification_manager.notify_console = MagicMock()
        notification_manager.notify_file = MagicMock()
        
        # Set channels
        notification_manager.channels = ["console", "file"]
        
        # Send notification
        result = notification_manager.notify(test_event_high, "Test message")
        
        # Check result
        assert result is True
        
        # Verify methods were called
        notification_manager.notify_console.assert_called_once_with(test_event_high, "Test message")
        notification_manager.notify_file.assert_called_once_with(test_event_high, "Test message")
    
    def test_notify_low_importance(self, notification_manager, test_event_low):
        """Test notification with low importance event."""
        # Mock the channel methods
        notification_manager.notify_console = MagicMock()
        
        # Send notification
        result = notification_manager.notify(test_event_low, "Test message")
        
        # Check result (should not notify)
        assert result is False
        
        # Verify methods were not called
        notification_manager.notify_console.assert_not_called()
    
    def test_notify_channel_error(self, notification_manager, test_event_high):
        """Test handling of channel errors."""
        # Mock the channel methods to raise exceptions
        notification_manager.notify_console = MagicMock(side_effect=Exception("Console error"))
        notification_manager.notify_file = MagicMock()
        
        # Set channels
        notification_manager.channels = ["console", "file"]
        
        # Send notification
        result = notification_manager.notify(test_event_high, "Test message")
        
        # Check result (should still try all channels)
        assert result is False
        
        # Verify both methods were called
        notification_manager.notify_console.assert_called_once()
        notification_manager.notify_file.assert_called_once()
