#!/usr/bin/env python3
"""
Test script to fetch real-time events from Aptos blockchain.
First tries the existing BlockchainMonitor, then falls back to direct SDK usage.
"""

import os
import sys
import json
import asyncio
import time
from datetime import datetime

# Add project root to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try importing from existing modules
from config import Config
from modules.blockchain import BlockchainMonitor, BlockchainEvent
from utils.logger import get_logger

# For direct SDK approach
from aptos_sdk.async_client import RestClient

logger = get_logger("aptos_events_test")

async def test_existing_monitor():
    """Test the existing BlockchainMonitor implementation."""
    print("\n===== Testing Existing BlockchainMonitor =====")
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize blockchain monitor
        monitor = BlockchainMonitor(config)
        
        print(f"Fetching events from Aptos blockchain using existing monitor...")
        events = monitor.fetch_events()
        
        if events:
            print(f"✅ Successfully fetched {len(events)} events using existing monitor")
            print("\nSample events:")
            for i, event in enumerate(events[:3]):  # Show up to 3 events
                print(f"\nEvent {i+1}:")
                print(f"  Type: {event.event_type}")
                print(f"  Category: {event.category}")
                print(f"  Importance: {event.importance_score}")
                print(f"  Timestamp: {event.timestamp}")
                print(f"  Data: {json.dumps(event.data, indent=2)[:200]}...")  # Truncate long data
            
            return True, events
        else:
            print("❌ No events fetched using existing monitor")
            return False, []
    except Exception as e:
        print(f"❌ Error using existing monitor: {str(e)}")
        return False, []

async def test_direct_sdk():
    """Test direct SDK approach for fetching events."""
    print("\n===== Testing Direct Aptos SDK Approach =====")
    try:
        # Initialize client with mainnet URL
        client = RestClient("https://fullnode.mainnet.aptoslabs.com/v1")
        
        # Test accounts and event handles
        test_accounts = [
            # Binance
            {
                "name": "Binance",
                "address": "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92",
                "handle": "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>",
                "field": "withdraw_events"
            },
            # Topaz NFT marketplace
            {
                "name": "Topaz NFT Marketplace",
                "address": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",
                "handle": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2::marketplace::ListingEvents",
                "field": "listing_events"
            }
        ]
        
        all_events = []
        
        for account in test_accounts:
            print(f"\nFetching events for {account['name']}...")
            try:
                # Fetch events with limit to avoid too many results
                events = await client.get_events_by_event_handle(
                    account["address"],
                    account["handle"],
                    account["field"],
                    limit=5  # Limit to 5 events for testing
                )
                
                print(f"✅ Successfully fetched {len(events)} events for {account['name']}")
                
                if events:
                    print(f"Sample event: {json.dumps(events[0], indent=2)[:200]}...")  # Truncate long data
                    
                    # Convert to BlockchainEvent objects for consistency
                    for event in events:
                        blockchain_event = BlockchainEvent.create_from_aptos_event({
                            "type": account["field"],
                            "data": event["data"]
                        })
                        all_events.append(blockchain_event)
            except Exception as e:
                print(f"❌ Error fetching events for {account['name']}: {str(e)}")
        
        if all_events:
            return True, all_events
        else:
            return False, []
    except Exception as e:
        print(f"❌ Error using direct SDK approach: {str(e)}")
        return False, []

async def test_websocket_approach():
    """Test WebSocket approach for real-time events."""
    print("\n===== Testing WebSocket Approach =====")
    try:
        import websockets
        
        uri = "wss://fullnode.mainnet.aptoslabs.com/v1/stream"
        
        print(f"Connecting to WebSocket at {uri}...")
        print("This will listen for real-time events. Press Ctrl+C to stop after seeing some events.")
        
        async with websockets.connect(uri) as websocket:
            # Subscribe to events
            await websocket.send(json.dumps({
                "method": "events.subscribe",
                "params": [
                    "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>",
                    "withdraw_events"
                ],
                "id": 1
            }))
            
            print("Subscription request sent. Waiting for events...")
            
            # Set a timeout for demonstration purposes
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
            
            # Process incoming events
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    event_data = json.loads(response)
                    print(f"\nReceived event: {json.dumps(event_data, indent=2)}")
                    
                    # If we got at least one event, consider it a success
                    if "result" in event_data:
                        return True, []
                except asyncio.TimeoutError:
                    # Just a timeout on the inner wait_for, continue listening
                    print(".", end="", flush=True)
                    continue
            
            print("\nNo events received within timeout period.")
            return False, []
    except Exception as e:
        print(f"❌ Error using WebSocket approach: {str(e)}")
        return False, []

async def test_rest_polling():
    """Test REST API polling approach."""
    print("\n===== Testing REST API Polling Approach =====")
    
    class AptosEventsPoller:
        def __init__(self, node_url="https://fullnode.mainnet.aptoslabs.com/v1"):
            self.node_url = node_url
            self.last_version = 0
            
        def get_latest_version(self):
            response = requests.get(f"{self.node_url}")
            return int(response.json().get("ledger_version", "0"))
        
        def fetch_events_by_handle(self, address, event_handle, field_name, limit=5):
            url = f"{self.node_url}/accounts/{address}/events/{event_handle}/{field_name}?limit={limit}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return []
    
    try:
        import requests
        
        poller = AptosEventsPoller()
        current_version = poller.get_latest_version()
        
        print(f"Current ledger version: {current_version}")
        
        # Test accounts and event handles
        test_accounts = [
            # Binance
            {
                "name": "Binance",
                "address": "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92",
                "handle": "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>",
                "field": "withdraw_events"
            },
            # Topaz NFT marketplace
            {
                "name": "Topaz NFT Marketplace",
                "address": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",
                "handle": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2::marketplace::ListingEvents",
                "field": "listing_events"
            }
        ]
        
        all_events = []
        
        for account in test_accounts:
            print(f"\nFetching events for {account['name']}...")
            events = poller.fetch_events_by_handle(
                account["address"],
                account["handle"],
                account["field"]
            )
            
            if events:
                print(f"✅ Found {len(events)} events for {account['name']}")
                print(f"Sample event: {json.dumps(events[0], indent=2)[:200]}...")  # Truncate long data
                
                # Convert to BlockchainEvent objects for consistency
                for event in events:
                    blockchain_event = BlockchainEvent.create_from_aptos_event({
                        "type": account["field"],
                        "data": event["data"]
                    })
                    all_events.append(blockchain_event)
            else:
                print(f"❌ No events found for {account['name']}")
        
        if all_events:
            return True, all_events
        else:
            return False, []
    except Exception as e:
        print(f"❌ Error using REST polling approach: {str(e)}")
        return False, []

async def main():
    """Main function to test different approaches."""
    print("=" * 80)
    print("APTOS BLOCKCHAIN EVENTS FETCHER TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Try existing monitor first
    success, events = await test_existing_monitor()
    
    # If existing monitor failed, try direct SDK approach
    if not success or not events:
        success, events = await test_direct_sdk()
    
    # If direct SDK failed, try REST polling
    if not success or not events:
        success, events = await test_rest_polling()
    
    # If all previous approaches failed, try WebSocket as last resort
    if not success or not events:
        success, _ = await test_websocket_approach()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ Successfully fetched real-time events from Aptos blockchain!")
    else:
        print("❌ Failed to fetch real-time events from Aptos blockchain.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
