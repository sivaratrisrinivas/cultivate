#!/usr/bin/env python3
"""
Comprehensive test script for the Discord bot module.
This script tests all functionality of the Discord bot, including:
1. Posting content to Discord
2. Handling user questions
3. Rate limiting and message queue processing
4. Event tracking to avoid duplicates
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from config import Config
from modules.blockchain import BlockchainEvent
from modules.ai import AIModule
from modules.discord_bot import DiscordBot
from utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Set up logging and console
logger = get_logger("discord_bot_test")
console = Console()

class DiscordBotTester:
    """Test suite for the Discord bot module."""
    
    def __init__(self):
        """Initialize the Discord bot tester."""
        console.print(Panel("Initializing Discord Bot Test Suite", title="Test Started", subtitle=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        
        # Create necessary directories
        for dir_path in ['data', 'cache', 'logs']:
            os.makedirs(dir_path, exist_ok=True)
        
        # Load configuration
        self.config = Config()
        
        # Check if Discord token is available
        if not self.config.DISCORD["BOT_TOKEN"]:
            console.print("[bold red]Discord bot token not available, some tests may be skipped[/bold red]")
        
        # Initialize AI module
        self.ai_module = AIModule(self.config)
        
        # Initialize Discord bot
        self.discord_bot = DiscordBot(self.config, self.ai_module)
    
    async def test_post_content(self):
        """Test the Discord bot's ability to post content."""
        console.print(Panel("Testing Post Content Functionality", title="Post Content Test"))
        
        # Create test content
        test_content = {
            "content": "This is a test post from the Aptos Social Media Manager! #Testing #Aptos",
            "event_reference": f"test_event_{asyncio.get_event_loop().time()}",
            "source_event": BlockchainEvent(
                "test_event", 
                "test", 
                {"test": True, "blockchain": "Aptos"}, 
                importance_score=0.7
            ).to_dict()
        }
        
        try:
            # Queue content for posting
            await self.discord_bot.post_content(test_content)
            
            # Check if content was added to the queue
            queue_size = self.discord_bot.message_queue.qsize()
            console.print(f"Message queue size after posting: {queue_size}")
            
            if queue_size > 0:
                console.print("✅ Content was successfully queued for posting")
                return True
            else:
                console.print("❌ Content was not added to the queue")
                return False
        except Exception as e:
            console.print(f"❌ Error posting content: {str(e)}")
            return False
    
    async def test_handle_question(self):
        """Test the Discord bot's ability to handle questions."""
        console.print(Panel("Testing Question Handling Functionality", title="Question Handling Test"))
        
        # Create test questions
        test_questions = [
            "What is Aptos?",
            "How does staking work on Aptos?",
            "Tell me about Move language"
        ]
        
        success_count = 0
        
        for i, question in enumerate(test_questions):
            console.print(f"\n[bold cyan]Testing question {i+1}:[/bold cyan] {question}")
            
            try:
                # Create a mock message
                mock_message = type('MockMessage', (), {
                    'content': f"{self.config.DISCORD['PREFIX']}ask {question}",
                    'channel': type('MockChannel', (), {
                        'send': lambda content: console.print(f"Would send to Discord: {content[:50]}...")
                    }),
                    'author': type('MockAuthor', (), {
                        'bot': False,
                        'mention': '@test_user'
                    })
                })
                
                # Process the message
                response = await self.discord_bot._handle_ask_command(mock_message, question)
                
                if response:
                    console.print("✅ Successfully handled question")
                    success_count += 1
                else:
                    console.print("❌ Failed to handle question")
            except Exception as e:
                console.print(f"❌ Error handling question: {str(e)}")
        
        console.print(f"\nSuccessfully handled {success_count} out of {len(test_questions)} questions")
        return success_count == len(test_questions)
    
    async def test_rate_limiting(self):
        """Test the Discord bot's rate limiting functionality."""
        console.print(Panel("Testing Rate Limiting Functionality", title="Rate Limiting Test"))
        
        # Create multiple test messages
        test_messages = [
            {
                "content": f"Test message {i} from the Aptos Social Media Manager! #Testing #Aptos",
                "event_reference": f"test_event_{i}_{asyncio.get_event_loop().time()}",
                "source_event": BlockchainEvent(
                    "test_event", 
                    "test", 
                    {"test": True, "blockchain": "Aptos", "sequence": i}, 
                    importance_score=0.7
                ).to_dict()
            } for i in range(5)
        ]
        
        try:
            # Queue multiple messages
            for message in test_messages:
                await self.discord_bot.post_content(message)
            
            # Check queue size
            queue_size = self.discord_bot.message_queue.qsize()
            console.print(f"Message queue size after posting multiple messages: {queue_size}")
            
            if queue_size == len(test_messages):
                console.print("✅ All messages were successfully queued")
                return True
            else:
                console.print(f"❌ Expected {len(test_messages)} messages in queue, but found {queue_size}")
                return False
        except Exception as e:
            console.print(f"❌ Error testing rate limiting: {str(e)}")
            return False
    
    async def test_duplicate_prevention(self):
        """Test the Discord bot's duplicate prevention functionality."""
        console.print(Panel("Testing Duplicate Prevention Functionality", title="Duplicate Prevention Test"))
        
        # Create a duplicate event
        duplicate_event_ref = f"duplicate_event_{asyncio.get_event_loop().time()}"
        duplicate_content = {
            "content": "This is a duplicate post test! #Testing #Aptos",
            "event_reference": duplicate_event_ref,
            "source_event": BlockchainEvent(
                "duplicate_event", 
                "test", 
                {"test": True, "blockchain": "Aptos"}, 
                importance_score=0.7
            ).to_dict()
        }
        
        try:
            # Post the same content twice
            await self.discord_bot.post_content(duplicate_content)
            first_queue_size = self.discord_bot.message_queue.qsize()
            
            # Add the event to posted events
            self.discord_bot.posted_events.add(duplicate_event_ref)
            
            # Try to post again
            await self.discord_bot.post_content(duplicate_content)
            second_queue_size = self.discord_bot.message_queue.qsize()
            
            console.print(f"Queue size after first post: {first_queue_size}")
            console.print(f"Queue size after second post: {second_queue_size}")
            
            if first_queue_size == second_queue_size:
                console.print("✅ Duplicate post was successfully prevented")
                return True
            else:
                console.print("❌ Duplicate post was not prevented")
                return False
        except Exception as e:
            console.print(f"❌ Error testing duplicate prevention: {str(e)}")
            return False

async def main():
    """Main function to run all tests."""
    try:
        # Initialize tester
        tester = DiscordBotTester()
        
        # Run tests
        tests = [
            ("Post Content", tester.test_post_content()),
            ("Handle Question", tester.test_handle_question()),
            ("Rate Limiting", tester.test_rate_limiting()),
            ("Duplicate Prevention", tester.test_duplicate_prevention())
        ]
        
        # Run all tests and collect results
        results = []
        for test_name, test_coro in tests:
            console.print(f"\n[bold]Running test: {test_name}[/bold]")
            try:
                result = await test_coro
                results.append((test_name, result))
            except Exception as e:
                console.print(f"❌ Test {test_name} failed with exception: {str(e)}")
                results.append((test_name, False))
        
        # Display results
        console.print("\n[bold]Test Results:[/bold]")
        table = Table(title="Discord Bot Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        
        success_count = 0
        for test_name, result in results:
            status = "✅ Passed" if result else "❌ Failed"
            color = "green" if result else "red"
            table.add_row(test_name, f"[{color}]{status}[/{color}]")
            if result:
                success_count += 1
        
        console.print(table)
        console.print(f"\n[bold]{'green' if success_count == len(results) else 'yellow'}]Summary: {success_count}/{len(results)} tests passed[/bold]")
        
        console.print(Panel("Discord Bot Test Suite Completed", title="Test Completed", subtitle=f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        
        # Return exit code based on test results
        return 0 if success_count == len(results) else 1
    except KeyboardInterrupt:
        console.print("\n[bold red]Test interrupted by user[/bold red]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]Test failed with exception: {str(e)}[/bold red]")
        return 2

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[bold red]Test interrupted by user[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Test failed with exception: {str(e)}[/bold red]")
        sys.exit(2)
