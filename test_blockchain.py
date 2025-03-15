#!/usr/bin/env python3
# test_blockchain.py
import os
import sys
import asyncio
import time
from config import Config
from modules.blockchain import BlockchainMonitor
from utils.logger import get_logger

# Set up logging
logger = get_logger("test_blockchain")

async def test_fetch_events():
    """Test the fetch_events method of the blockchain monitor."""
    logger.info("Testing fetch_events method")
    
    # Load configuration
    config = Config()
    
    # Initialize blockchain monitor
    monitor = BlockchainMonitor(config)
    
    # Fetch events
    events = await monitor.fetch_events_async()
    
    if events:
        logger.info(f"Successfully fetched {len(events)} events")
        for i, event in enumerate(events):
            logger.info(f"Event {i+1}: {event.event_type}")
            logger.info(f"Event data: {event.data}")
            logger.info(f"Importance score: {event.importance_score}")
    else:
        logger.info("No events fetched")
    
    return len(events) > 0

async def test_sdk_fetch():
    """Test the SDK-based fetch method."""
    logger.info("Testing SDK-based fetch method")
    
    # Load configuration
    config = Config()
    
    # Initialize blockchain monitor
    monitor = BlockchainMonitor(config)
    
    # Fetch events using SDK
    events = await monitor.fetch_events_with_sdk()
    
    if events:
        logger.info(f"Successfully fetched {len(events)} events using SDK")
        for i, event in enumerate(events):
            logger.info(f"Event {i+1}: {event.event_type}")
            logger.info(f"Event data: {event.data}")
    else:
        logger.info("No events fetched using SDK")
    
    return len(events) > 0

async def test_rest_fetch():
    """Test the REST-based fetch method."""
    logger.info("Testing REST-based fetch method")
    
    # Load configuration
    config = Config()
    
    # Initialize blockchain monitor
    monitor = BlockchainMonitor(config)
    
    # Fetch events using REST
    events = await monitor.fetch_events_with_rest()
    
    if events:
        logger.info(f"Successfully fetched {len(events)} events using REST API")
        for i, event in enumerate(events):
            logger.info(f"Event {i+1}: {event.event_type}")
            logger.info(f"Event data: {event.data}")
    else:
        logger.info("No events fetched using REST API")
    
    return len(events) > 0

async def main():
    """Run all tests."""
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Test SDK fetch method
    sdk_success = await test_sdk_fetch()
    
    # Test REST fetch method
    rest_success = await test_rest_fetch()
    
    # Test combined fetch_events method
    fetch_success = await test_fetch_events()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"SDK Fetch Test: {'PASSED' if sdk_success else 'FAILED'}")
    logger.info(f"REST Fetch Test: {'PASSED' if rest_success else 'FAILED'}")
    logger.info(f"Combined Fetch Events Test: {'PASSED' if fetch_success else 'FAILED'}")
    
    if sdk_success or rest_success:
        logger.info("At least one fetch method PASSED!")
        return 0
    else:
        logger.error("All fetch methods FAILED!")
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
