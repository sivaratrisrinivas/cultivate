#!/usr/bin/env python3
# test_discord_bot.py
import os
import sys
import asyncio
from config import Config
from modules.blockchain import BlockchainEvent
from modules.ai import AIModule
from modules.discord_bot import DiscordBot
from utils.logger import get_logger

# Set up logging
logger = get_logger("test_discord_bot")

async def test_post_content():
    """Test the Discord bot's ability to post content."""
    logger.info("Testing post_content method")
    
    # Load configuration
    config = Config()
    
    # Check if Discord token is available
    if not config.DISCORD["BOT_TOKEN"]:
        logger.warning("Discord bot token not available, skipping test")
        return False
    
    # Initialize AI module
    ai_module = AIModule(config)
    
    # Initialize Discord bot
    discord_bot = DiscordBot(config, ai_module)
    
    # Create test content
    test_content = {
        "content": "This is a test post from the Aptos Social Media Manager! #Testing #Aptos",
        "event_reference": f"test_event_{asyncio.get_event_loop().time()}",
        "source_event": BlockchainEvent("test_event", {"test": True}, 0.7).to_dict()
    }
    
    try:
        # Queue content for posting
        await discord_bot.post_content(test_content)
        
        # Check if content was added to the queue
        queue_size = discord_bot.message_queue.qsize()
        logger.info(f"Message queue size after posting: {queue_size}")
        
        if queue_size > 0:
            logger.info("Content was successfully queued for posting")
            return True
        else:
            logger.error("Content was not added to the queue")
            return False
    except Exception as e:
        logger.error(f"Error posting content: {str(e)}")
        return False

async def test_handle_question():
    """Test the Discord bot's ability to handle questions."""
    logger.info("Testing _handle_potential_question method")
    
    # Load configuration
    config = Config()
    
    # Check if Discord token is available
    if not config.DISCORD["BOT_TOKEN"]:
        logger.warning("Discord bot token not available, skipping test")
        return False
    
    # Initialize AI module
    ai_module = AIModule(config)
    
    # Initialize Discord bot
    discord_bot = DiscordBot(config, ai_module)
    
    # Create mock message class
    class MockMessage:
        def __init__(self, content, mentions=None):
            self.content = content
            self.mentions = mentions or []
            self.author = MockUser()
        
        async def reply(self, text):
            logger.info(f"Mock reply: {text}")
            return True
    
    class MockUser:
        def __init__(self):
            self.id = 12345
    
    # Create test messages
    test_messages = [
        MockMessage("What is Aptos blockchain?"),
        MockMessage("How do I create a wallet on Aptos?"),
        MockMessage("Hello, can you tell me about Aptos?", [discord_bot.bot.user])
    ]
    
    success = True
    
    for i, message in enumerate(test_messages):
        logger.info(f"Testing message {i+1}: {message.content}")
        
        try:
            # Handle the message
            await discord_bot._handle_potential_question(message)
            logger.info(f"Message {i+1} handled successfully")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            success = False
    
    return success

async def main():
    """Run all tests."""
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('cache', exist_ok=True)
    
    # Test post_content method
    post_success = await test_post_content()
    
    # Test handle_question method
    question_success = await test_handle_question()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Post Content Test: {'PASSED' if post_success else 'FAILED'}")
    logger.info(f"Handle Question Test: {'PASSED' if question_success else 'FAILED'}")
    
    if post_success and question_success:
        logger.info("All tests PASSED!")
        return 0
    else:
        logger.error("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
