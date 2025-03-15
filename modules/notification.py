"""
Notification module for the Cultivate project.
Handles sending notifications about blockchain events through various channels.
"""

import os
import json
import logging
import requests
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)

class NotificationManager:
    """
    Manages notifications for blockchain events.
    Supports multiple notification channels: console, file, webhook, Discord, Slack.
    """
    
    def __init__(self, config):
        """
        Initialize the notification manager.
        
        Args:
            config: Configuration object containing notification settings
        """
        self.enabled = config.NOTIFICATIONS.get("ENABLED", True)
        self.channels = config.NOTIFICATIONS.get("CHANNELS", ["console"])
        self.min_importance = config.NOTIFICATIONS.get("MIN_IMPORTANCE", 0.7)
        
        # Optional webhook URLs
        self.webhook_url = config.NOTIFICATIONS.get("WEBHOOK_URL", None)
        self.discord_webhook_url = config.NOTIFICATIONS.get("DISCORD_WEBHOOK_URL", None)
        self.slack_webhook_url = config.NOTIFICATIONS.get("SLACK_WEBHOOK_URL", None)
        
        # Notification log file
        self.log_file = config.NOTIFICATIONS.get("LOG_FILE", "notifications.log")
        
        logger.info(f"Notification manager initialized with channels: {self.channels}")
    
    def should_notify(self, event):
        """
        Determine if a notification should be sent for an event.
        
        Args:
            event: BlockchainEvent object
            
        Returns:
            bool: True if notification should be sent
        """
        if not self.enabled:
            return False
            
        return event.importance_score >= self.min_importance
    
    def notify(self, event, message):
        """
        Send a notification for an event through all configured channels.
        
        Args:
            event: BlockchainEvent object
            message: Notification message
            
        Returns:
            bool: True if notification was sent successfully
        """
        if not self.should_notify(event):
            logger.debug(f"Skipping notification for event {event.event_type} (importance: {event.importance_score})")
            return False
        
        logger.info(f"Sending notification for event {event.event_type}")
        
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
                else:
                    logger.warning(f"Unknown or unconfigured notification channel: {channel}")
            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {str(e)}")
                success = False
        
        return success
    
    def _format_message(self, event, message):
        """
        Format a notification message.
        
        Args:
            event: BlockchainEvent object
            message: Notification message
            
        Returns:
            str: Formatted message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted = f"[{timestamp}] {event.event_type.upper()} ({event.category})\n"
        formatted += f"Importance: {event.importance_score:.2f}\n"
        formatted += f"Message: {message}\n"
        
        # Add event details
        formatted += f"Details: {json.dumps(event.data, indent=2)}\n"
        
        return formatted
    
    def notify_console(self, event, message):
        """
        Send a notification to the console.
        
        Args:
            event: BlockchainEvent object
            message: Notification message
        """
        formatted = self._format_message(event, message)
        print(f"\n{'=' * 80}\nNOTIFICATION\n{'=' * 80}\n{formatted}\n{'=' * 80}\n")
    
    def notify_file(self, event, message):
        """
        Send a notification to a log file.
        
        Args:
            event: BlockchainEvent object
            message: Notification message
        """
        formatted = self._format_message(event, message)
        
        with open(self.log_file, "a") as f:
            f.write(f"{formatted}\n{'=' * 80}\n")
    
    def notify_webhook(self, event, message):
        """
        Send a notification to a webhook.
        
        Args:
            event: BlockchainEvent object
            message: Notification message
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event.event_type,
            "category": event.category,
            "importance": event.importance_score,
            "message": message,
            "details": event.data
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
    
    def notify_discord(self, event, message):
        """
        Send a notification to Discord.
        
        Args:
            event: BlockchainEvent object
            message: Notification message
        """
        formatted = self._format_message(event, message)
        
        payload = {
            "content": f"```\n{formatted}\n```",
            "username": "Cultivate Monitor",
            "embeds": [
                {
                    "title": f"{event.event_type.upper()} Event",
                    "description": message,
                    "color": 5814783,
                    "fields": [
                        {
                            "name": "Category",
                            "value": event.category,
                            "inline": True
                        },
                        {
                            "name": "Importance",
                            "value": f"{event.importance_score:.2f}",
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": f"Cultivate Monitor • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }
            ]
        }
        
        response = requests.post(
            self.discord_webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
    
    def notify_slack(self, event, message):
        """
        Send a notification to Slack.
        
        Args:
            event: BlockchainEvent object
            message: Notification message
        """
        formatted = self._format_message(event, message)
        
        payload = {
            "text": f"*{event.event_type.upper()} Event*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{event.event_type.upper()} Event"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Category:*\n{event.category}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Importance:*\n{event.importance_score:.2f}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{json.dumps(event.data, indent=2)}```"
                    }
                }
            ]
        }
        
        response = requests.post(
            self.slack_webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
