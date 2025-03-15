#!/usr/bin/env python3
"""
Comprehensive test script for the Notification module.
This script tests all functionality of the notification module, including:
1. Console notifications
2. File notifications
3. Webhook notifications
4. Discord webhook notifications
5. Slack webhook notifications
6. Notification filtering based on importance
"""

import os
import sys
import json
import asyncio
import requests
from datetime import datetime
from unittest.mock import patch, MagicMock
from config import Config
from modules.blockchain import BlockchainEvent
from modules.notification import NotificationManager
from utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Set up logging and console
logger = get_logger("notification_test")
console = Console()

class NotificationTester:
    """Test suite for the Notification module."""
    
    def __init__(self):
        """Initialize the notification tester."""
        console.print(Panel("Initializing Notification Test Suite", title="Test Started", subtitle=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        
        # Create necessary directories
        for dir_path in ['data', 'logs']:
            os.makedirs(dir_path, exist_ok=True)
        
        # Load configuration
        self.config = Config()
        
        # Initialize notification manager
        self.notification_manager = NotificationManager(self.config)
        
        # Create test events
        self.test_events = self._create_test_events()
    
    def _create_test_events(self):
        """Create test blockchain events with varying importance scores."""
        return [
            BlockchainEvent(
                "nft_mint", 
                "nft", 
                {
                    "blockchain": "Aptos",
                    "collection_name": "Aptos Monkeys",
                    "creator": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",
                    "name": "Aptos Monkey #1234",
                    "amount": 1,
                    "type": "NFT_MINT"
                },
                importance_score=0.9
            ),
            BlockchainEvent(
                "token_event", 
                "transfer", 
                {
                    "blockchain": "Aptos",
                    "amount": 1500000,
                    "token_name": "APT",
                    "from": "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92",
                    "to": "0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4",
                    "event_subtype": "large_transfer"
                },
                importance_score=0.8
            ),
            BlockchainEvent(
                "contract_event", 
                "deployment", 
                {
                    "blockchain": "Aptos",
                    "address": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",
                    "module_name": "marketplace",
                    "event_subtype": "contract_deployed"
                },
                importance_score=0.7
            ),
            BlockchainEvent(
                "governance_event", 
                "proposal", 
                {
                    "blockchain": "Aptos",
                    "proposal_id": "AIP-12345",
                    "title": "Increase staking rewards",
                    "proposer": "0x1",
                    "event_subtype": "proposal_created"
                },
                importance_score=0.6
            )
        ]
    
    def test_initialization(self):
        """Test initialization of the notification manager."""
        console.print(Panel("Testing Notification Manager Initialization", title="Initialization Test"))
        
        try:
            # Check if notification manager was initialized correctly
            console.print(f"Notification channels: {self.notification_manager.channels}")
            console.print(f"Minimum importance threshold: {self.notification_manager.min_importance}")
            console.print(f"Notifications enabled: {self.notification_manager.enabled}")
            
            if self.notification_manager.enabled:
                console.print("✅ Notification manager initialized successfully")
                return True
            else:
                console.print("❌ Notification manager is disabled")
                return False
        except Exception as e:
            console.print(f"❌ Error during initialization test: {str(e)}")
            return False
    
    def test_should_notify(self):
        """Test the should_notify method with events of varying importance."""
        console.print(Panel("Testing Notification Filtering", title="Importance Filtering Test"))
        
        results = []
        
        # Test with notifications enabled
        with patch.object(self.notification_manager, 'enabled', True):
            for i, event in enumerate(self.test_events):
                should_notify = self.notification_manager.should_notify(event)
                console.print(f"Event {i+1} (importance: {event.importance_score}): {'Should notify' if should_notify else 'Should not notify'}")
                results.append(should_notify)
        
        # Test with notifications disabled
        with patch.object(self.notification_manager, 'enabled', False):
            event = self.test_events[0]  # Use the highest importance event
            should_notify = self.notification_manager.should_notify(event)
            console.print(f"With notifications disabled: {'Should notify' if should_notify else 'Should not notify'}")
            results.append(not should_notify)  # Should be False when disabled
        
        # Check if results match expectations
        expected_results = [
            event.importance_score >= self.notification_manager.min_importance 
            for event in self.test_events
        ] + [False]  # Add expected result for disabled test
        
        success = results == expected_results
        if success:
            console.print("✅ Notification filtering works correctly")
        else:
            console.print("❌ Notification filtering does not work as expected")
        
        return success
    
    def test_console_notification(self):
        """Test console notifications."""
        console.print(Panel("Testing Console Notifications", title="Console Notification Test"))
        
        try:
            # Patch the print function to capture output
            with patch('builtins.print') as mock_print:
                # Set channels to console only
                with patch.object(self.notification_manager, 'channels', ['console']):
                    # Use a high importance event
                    event = self.test_events[0]
                    
                    # Send notification
                    self.notification_manager.notify(event)
                    
                    # Check if print was called
                    if mock_print.called:
                        console.print("✅ Console notification was sent")
                        return True
                    else:
                        console.print("❌ Console notification was not sent")
                        return False
        except Exception as e:
            console.print(f"❌ Error during console notification test: {str(e)}")
            return False
    
    def test_file_notification(self):
        """Test file notifications."""
        console.print(Panel("Testing File Notifications", title="File Notification Test"))
        
        try:
            # Create a temporary log file
            test_log_file = "test_notifications.log"
            
            # Set channels to file only and set log file
            with patch.object(self.notification_manager, 'channels', ['file']), \
                 patch.object(self.notification_manager, 'log_file', test_log_file):
                
                # Use a high importance event
                event = self.test_events[0]
                
                # Send notification
                self.notification_manager.notify(event)
                
                # Check if file was created and contains notification
                if os.path.exists(test_log_file):
                    with open(test_log_file, 'r') as f:
                        content = f.read()
                    
                    if event.event_type in content:
                        console.print("✅ File notification was sent")
                        # Clean up
                        os.remove(test_log_file)
                        return True
                    else:
                        console.print("❌ File notification was sent but content is incorrect")
                        # Clean up
                        os.remove(test_log_file)
                        return False
                else:
                    console.print("❌ File notification was not sent")
                    return False
        except Exception as e:
            console.print(f"❌ Error during file notification test: {str(e)}")
            # Clean up if file exists
            if os.path.exists(test_log_file):
                os.remove(test_log_file)
            return False
    
    def test_webhook_notification(self):
        """Test webhook notifications."""
        console.print(Panel("Testing Webhook Notifications", title="Webhook Notification Test"))
        
        try:
            # Mock the requests.post method
            with patch('requests.post') as mock_post:
                # Set up the mock response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response
                
                # Set channels to webhook only and set webhook URL
                with patch.object(self.notification_manager, 'channels', ['webhook']), \
                     patch.object(self.notification_manager, 'webhook_url', 'https://example.com/webhook'):
                    
                    # Use a high importance event
                    event = self.test_events[0]
                    
                    # Send notification
                    self.notification_manager.notify(event)
                    
                    # Check if requests.post was called with the correct URL
                    if mock_post.called and mock_post.call_args[0][0] == 'https://example.com/webhook':
                        console.print("✅ Webhook notification was sent")
                        return True
                    else:
                        console.print("❌ Webhook notification was not sent")
                        return False
        except Exception as e:
            console.print(f"❌ Error during webhook notification test: {str(e)}")
            return False
    
    def test_discord_notification(self):
        """Test Discord webhook notifications."""
        console.print(Panel("Testing Discord Notifications", title="Discord Notification Test"))
        
        try:
            # Mock the requests.post method
            with patch('requests.post') as mock_post:
                # Set up the mock response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response
                
                # Set channels to discord only and set Discord webhook URL
                with patch.object(self.notification_manager, 'channels', ['discord']), \
                     patch.object(self.notification_manager, 'discord_webhook_url', 'https://discord.com/api/webhooks/example'):
                    
                    # Use a high importance event
                    event = self.test_events[0]
                    
                    # Send notification
                    self.notification_manager.notify(event)
                    
                    # Check if requests.post was called with the correct URL
                    if mock_post.called and mock_post.call_args[0][0] == 'https://discord.com/api/webhooks/example':
                        console.print("✅ Discord notification was sent")
                        return True
                    else:
                        console.print("❌ Discord notification was not sent")
                        return False
        except Exception as e:
            console.print(f"❌ Error during Discord notification test: {str(e)}")
            return False
    
    def test_slack_notification(self):
        """Test Slack webhook notifications."""
        console.print(Panel("Testing Slack Notifications", title="Slack Notification Test"))
        
        try:
            # Mock the requests.post method
            with patch('requests.post') as mock_post:
                # Set up the mock response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response
                
                # Set channels to slack only and set Slack webhook URL
                with patch.object(self.notification_manager, 'channels', ['slack']), \
                     patch.object(self.notification_manager, 'slack_webhook_url', 'https://hooks.slack.com/services/example'):
                    
                    # Use a high importance event
                    event = self.test_events[0]
                    
                    # Send notification
                    self.notification_manager.notify(event)
                    
                    # Check if requests.post was called with the correct URL
                    if mock_post.called and mock_post.call_args[0][0] == 'https://hooks.slack.com/services/example':
                        console.print("✅ Slack notification was sent")
                        return True
                    else:
                        console.print("❌ Slack notification was not sent")
                        return False
        except Exception as e:
            console.print(f"❌ Error during Slack notification test: {str(e)}")
            return False
    
    def test_multiple_channels(self):
        """Test notifications through multiple channels."""
        console.print(Panel("Testing Multiple Notification Channels", title="Multiple Channels Test"))
        
        try:
            # Mock the requests.post method and print function
            with patch('requests.post') as mock_post, patch('builtins.print') as mock_print:
                # Set up the mock response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response
                
                # Set channels to multiple channels
                with patch.object(self.notification_manager, 'channels', ['console', 'discord', 'slack']), \
                     patch.object(self.notification_manager, 'discord_webhook_url', 'https://discord.com/api/webhooks/example'), \
                     patch.object(self.notification_manager, 'slack_webhook_url', 'https://hooks.slack.com/services/example'):
                    
                    # Use a high importance event
                    event = self.test_events[0]
                    
                    # Send notification
                    self.notification_manager.notify(event)
                    
                    # Check if all channels were used
                    console_used = mock_print.called
                    discord_used = any(call[0][0] == 'https://discord.com/api/webhooks/example' for call in mock_post.call_args_list)
                    slack_used = any(call[0][0] == 'https://hooks.slack.com/services/example' for call in mock_post.call_args_list)
                    
                    if console_used and discord_used and slack_used:
                        console.print("✅ Notifications were sent through all channels")
                        return True
                    else:
                        console.print("❌ Notifications were not sent through all channels")
                        console.print(f"Console: {'✅' if console_used else '❌'}")
                        console.print(f"Discord: {'✅' if discord_used else '❌'}")
                        console.print(f"Slack: {'✅' if slack_used else '❌'}")
                        return False
        except Exception as e:
            console.print(f"❌ Error during multiple channels test: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling in notification methods."""
        console.print(Panel("Testing Error Handling", title="Error Handling Test"))
        
        try:
            # Test with invalid webhook URL
            with patch.object(self.notification_manager, 'channels', ['webhook']), \
                 patch.object(self.notification_manager, 'webhook_url', 'invalid://url'), \
                 patch('requests.post', side_effect=requests.exceptions.RequestException("Test exception")):
                
                # Use a high importance event
                event = self.test_events[0]
                
                # Send notification (should not raise exception)
                try:
                    self.notification_manager.notify(event)
                    console.print("✅ Error was handled gracefully")
                    return True
                except Exception as e:
                    console.print(f"❌ Error was not handled gracefully: {str(e)}")
                    return False
        except Exception as e:
            console.print(f"❌ Error during error handling test: {str(e)}")
            return False

def main():
    """Main function to run all tests."""
    try:
        # Initialize tester
        tester = NotificationTester()
        
        # Run tests
        tests = [
            ("Initialization", tester.test_initialization()),
            ("Should Notify", tester.test_should_notify()),
            ("Console Notification", tester.test_console_notification()),
            ("File Notification", tester.test_file_notification()),
            ("Webhook Notification", tester.test_webhook_notification()),
            ("Discord Notification", tester.test_discord_notification()),
            ("Slack Notification", tester.test_slack_notification()),
            ("Multiple Channels", tester.test_multiple_channels()),
            ("Error Handling", tester.test_error_handling())
        ]
        
        # Display results
        console.print("\n[bold]Test Results:[/bold]")
        table = Table(title="Notification Module Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        
        success_count = 0
        for test_name, result in tests:
            status = "✅ Passed" if result else "❌ Failed"
            color = "green" if result else "red"
            table.add_row(test_name, f"[{color}]{status}[/{color}]")
            if result:
                success_count += 1
        
        console.print(table)
        console.print(f"\n[{'green' if success_count == len(tests) else 'yellow'}]Summary: {success_count}/{len(tests)} tests passed[/{'green' if success_count == len(tests) else 'yellow'}]")
        
        console.print(Panel("Notification Module Test Suite Completed", title="Test Completed", subtitle=f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        
        # Return exit code based on test results
        return 0 if success_count == len(tests) else 1
    except KeyboardInterrupt:
        console.print("\n[bold red]Test interrupted by user[/bold red]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]Test failed with exception: {str(e)}[/bold red]")
        return 2

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[bold red]Test interrupted by user[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Test failed with exception: {str(e)}[/bold red]")
        sys.exit(2)
