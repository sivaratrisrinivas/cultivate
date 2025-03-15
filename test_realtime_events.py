#!/usr/bin/env python3
# test_realtime_events.py
import os
import sys
import asyncio
import time
import json
import requests
from datetime import datetime, timedelta
from config import Config
from modules.blockchain import BlockchainMonitor, BlockchainEvent
from utils.logger import get_logger

# Set up logging
logger = get_logger("test_realtime_events")

class RealtimeEventTester:
    """Test the blockchain module's ability to fetch real-time events."""
    
    def __init__(self):
        """Initialize the tester."""
        # Load configuration
        self.config = Config()
        
        # Initialize blockchain monitor
        self.blockchain_monitor = BlockchainMonitor(self.config)
        
        # Aptos explorer API for verification
        self.explorer_api = "https://api.aptoscan.com"
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    async def fetch_events_continuously(self, duration_seconds=120, interval_seconds=10):
        """Fetch events continuously for a specified duration."""
        logger.info(f"Fetching events continuously for {duration_seconds} seconds with {interval_seconds} second intervals")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        all_events = []
        iteration = 1
        
        while time.time() < end_time:
            logger.info(f"Iteration {iteration}: Fetching events...")
            
            # Fetch events
            events = await self.blockchain_monitor.fetch_events_async()
            
            if events:
                logger.info(f"Found {len(events)} events in iteration {iteration}")
                
                # Print event details
                for i, event in enumerate(events):
                    logger.info(f"Event {i+1}: {event.event_type}")
                    logger.info(f"  Timestamp: {event.timestamp}")
                    logger.info(f"  Importance: {event.importance_score}")
                    logger.info(f"  Data: {json.dumps(event.data, indent=2)}")
                    
                    # Add to all events
                    all_events.append(event)
            else:
                logger.info(f"No events found in iteration {iteration}")
            
            # Wait for next interval
            iteration += 1
            await asyncio.sleep(interval_seconds)
        
        logger.info(f"Completed {iteration-1} iterations. Found a total of {len(all_events)} events.")
        return all_events
    
    async def verify_events_with_explorer(self, events):
        """Verify events by comparing with Aptos Explorer API."""
        if not events:
            logger.info("No events to verify")
            return False
        
        logger.info(f"Verifying {len(events)} events with Aptos Explorer API")
        
        # Get current time
        current_time = datetime.now()
        
        # Calculate time window (last hour)
        start_time = current_time - timedelta(hours=1)
        
        # Format times for API
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Get transactions from explorer
        try:
            # Construct URL for recent transactions
            url = f"{self.explorer_api}/v1/transactions"
            params = {
                "start_time": start_time_str,
                "limit": 100
            }
            
            # Fetch transactions
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch transactions from explorer: {response.status_code}")
                return False
            
            transactions = response.json()
            logger.info(f"Fetched {len(transactions)} recent transactions from explorer")
            
            # Extract transaction hashes
            explorer_tx_hashes = set()
            for tx in transactions:
                if "hash" in tx:
                    explorer_tx_hashes.add(tx["hash"])
            
            # Extract transaction hashes from our events
            our_tx_hashes = set()
            for event in events:
                if "transaction_hash" in event.data:
                    our_tx_hashes.add(event.data["transaction_hash"])
            
            # Find intersection
            common_tx_hashes = explorer_tx_hashes.intersection(our_tx_hashes)
            
            if common_tx_hashes:
                logger.info(f"Found {len(common_tx_hashes)} matching transaction hashes between our events and explorer")
                logger.info(f"Matching transaction hashes: {common_tx_hashes}")
                return True
            else:
                logger.info("No matching transaction hashes found")
                
                # If we don't have transaction hashes, check for event types
                explorer_event_types = set()
                for tx in transactions:
                    if "events" in tx:
                        for event in tx["events"]:
                            if "type" in event:
                                explorer_event_types.add(event["type"])
                
                our_event_types = set()
                for event in events:
                    if "type" in event.data:
                        our_event_types.add(event.data["type"])
                
                common_event_types = explorer_event_types.intersection(our_event_types)
                
                if common_event_types:
                    logger.info(f"Found {len(common_event_types)} matching event types between our events and explorer")
                    logger.info(f"Matching event types: {common_event_types}")
                    return True
                else:
                    logger.info("No matching event types found")
                    return False
            
        except Exception as e:
            logger.error(f"Error verifying events with explorer: {str(e)}")
            return False
    
    async def compare_consecutive_fetches(self):
        """Compare two consecutive fetches to verify real-time updates."""
        logger.info("Comparing consecutive fetches to verify real-time updates")
        
        # First fetch
        logger.info("Performing first fetch...")
        events1 = await self.blockchain_monitor.fetch_events_async()
        
        if not events1:
            logger.info("No events found in first fetch")
            return False
        
        logger.info(f"Found {len(events1)} events in first fetch")
        
        # Wait for 30 seconds
        logger.info("Waiting for 30 seconds before second fetch...")
        await asyncio.sleep(30)
        
        # Second fetch
        logger.info("Performing second fetch...")
        events2 = await self.blockchain_monitor.fetch_events_async()
        
        if not events2:
            logger.info("No events found in second fetch")
            return False
        
        logger.info(f"Found {len(events2)} events in second fetch")
        
        # Compare events
        events1_ids = set([f"{e.event_type}_{e.timestamp}" for e in events1])
        events2_ids = set([f"{e.event_type}_{e.timestamp}" for e in events2])
        
        new_events = events2_ids - events1_ids
        
        if new_events:
            logger.info(f"Found {len(new_events)} new events in second fetch")
            return True
        else:
            logger.info("No new events found in second fetch")
            return False
    
    async def check_event_timestamps(self, events):
        """Check if event timestamps are recent."""
        if not events:
            logger.info("No events to check timestamps")
            return False
        
        logger.info(f"Checking timestamps of {len(events)} events")
        
        # Get current time
        current_time = datetime.now()
        
        # Calculate time window (last hour)
        one_hour_ago = current_time - timedelta(hours=1)
        
        # Check event timestamps
        recent_events = 0
        for event in events:
            try:
                event_time = datetime.fromisoformat(event.timestamp)
                if event_time > one_hour_ago:
                    recent_events += 1
            except Exception as e:
                logger.error(f"Error parsing event timestamp: {str(e)}")
        
        logger.info(f"Found {recent_events} events with timestamps in the last hour")
        
        return recent_events > 0
    
    async def run_tests(self):
        """Run all tests."""
        logger.info("Starting real-time event tests")
        
        # Test 1: Fetch events continuously
        logger.info("\n=== Test 1: Fetch Events Continuously ===")
        events = await self.fetch_events_continuously(duration_seconds=60, interval_seconds=10)
        test1_success = len(events) > 0
        
        # Test 2: Verify events with explorer
        logger.info("\n=== Test 2: Verify Events with Explorer ===")
        test2_success = await self.verify_events_with_explorer(events)
        
        # Test 3: Compare consecutive fetches
        logger.info("\n=== Test 3: Compare Consecutive Fetches ===")
        test3_success = await self.compare_consecutive_fetches()
        
        # Test 4: Check event timestamps
        logger.info("\n=== Test 4: Check Event Timestamps ===")
        test4_success = await self.check_event_timestamps(events)
        
        # Print summary
        logger.info("\n=== Real-time Event Test Summary ===")
        logger.info(f"Test 1 (Fetch Events Continuously): {'PASSED' if test1_success else 'FAILED'}")
        logger.info(f"Test 2 (Verify Events with Explorer): {'PASSED' if test2_success else 'FAILED'}")
        logger.info(f"Test 3 (Compare Consecutive Fetches): {'PASSED' if test3_success else 'FAILED'}")
        logger.info(f"Test 4 (Check Event Timestamps): {'PASSED' if test4_success else 'FAILED'}")
        
        # Overall result
        overall_success = test1_success and (test2_success or test3_success or test4_success)
        
        if overall_success:
            logger.info("\nOverall result: PASSED - The blockchain module is fetching real-time events!")
            return 0
        else:
            logger.error("\nOverall result: FAILED - The blockchain module may not be fetching real-time events.")
            return 1

async def main():
    """Run the real-time event tests."""
    tester = RealtimeEventTester()
    return await tester.run_tests()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
