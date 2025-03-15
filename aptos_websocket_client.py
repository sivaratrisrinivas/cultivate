#!/usr/bin/env python3
"""
Aptos WebSocket Client
Provides real-time event monitoring for Aptos blockchain using WebSockets
with fallback to REST API polling.
"""

import json
import asyncio
import websockets
import logging
import requests
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class AptosWebSocketClient:
    """Client for real-time Aptos blockchain event monitoring using WebSockets."""
    
    def __init__(self, node_url="https://fullnode.mainnet.aptoslabs.com/v1", 
                 ws_url="wss://fullnode.mainnet.aptoslabs.com/v1/stream",
                 reconnect_delay=5,
                 fallback_poll_interval=60):
        """Initialize the WebSocket client with fallback options."""
        self.node_url = node_url
        self.ws_url = ws_url
        self.reconnect_delay = reconnect_delay
        self.fallback_poll_interval = fallback_poll_interval
        self.last_version_file = "last_version.txt"
        self.websocket_available = True
        self.subscriptions = []
        self.event_handlers = []
        self.running = False
        
    def register_event_handler(self, handler):
        """Register a callback function to handle events."""
        if callable(handler):
            self.event_handlers.append(handler)
            return True
        return False
    
    def subscribe_to_events(self, event_type, account=None, event_handle=None, field_name=None):
        """Add a subscription for specific events."""
        subscription = {
            "type": event_type,
            "account": account,
            "event_handle": event_handle,
            "field_name": field_name
        }
        self.subscriptions.append(subscription)
        logger.info(f"Added subscription: {subscription}")
        return subscription
        
    def get_last_processed_version(self):
        """Get the last processed blockchain version."""
        try:
            with open(self.last_version_file, "r") as f:
                return int(f.read().strip())
        except:
            return 0
            
    def save_last_processed_version(self, version):
        """Save the last processed blockchain version."""
        with open(self.last_version_file, "w") as f:
            f.write(str(version))
    
    def get_latest_version(self):
        """Get the latest blockchain version from the node."""
        try:
            response = requests.get(f"{self.node_url}")
            if response.status_code == 200:
                return int(response.json().get("ledger_version", "0"))
            else:
                logger.error(f"Failed to get latest version: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"Error getting latest version: {str(e)}")
            return 0
    
    def get_account(self, address):
        """Get account information."""
        try:
            url = f"{self.node_url}/accounts/{address}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting account {address}: {str(e)}")
            return None
    
    def get_account_resources(self, address):
        """Get resources for an account."""
        try:
            url = f"{self.node_url}/accounts/{address}/resources"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting resources for account {address}: {str(e)}")
            return None
    
    def get_events_by_event_handle(self, address, event_handle, field_name, start=None, limit=100):
        """Get events by event handle using REST API."""
        try:
            url = f"{self.node_url}/accounts/{address}/events/{event_handle}/{field_name}"
            params = {}
            if start is not None:
                params['start'] = start
            if limit is not None:
                params['limit'] = limit
                
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching events: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching events: {str(e)}")
            return []
    
    def get_transactions(self, start_version, limit=100):
        """Get transactions from the blockchain."""
        try:
            url = f"{self.node_url}/transactions"
            params = {
                'start': start_version,
                'limit': limit
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching transactions: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching transactions: {str(e)}")
            return []
    
    def get_transaction_by_hash(self, txn_hash):
        """Get a transaction by its hash."""
        try:
            url = f"{self.node_url}/transactions/by_hash/{txn_hash}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting transaction {txn_hash}: {str(e)}")
            return None
    
    def get_transaction_by_version(self, version):
        """Get a transaction by its version."""
        try:
            url = f"{self.node_url}/transactions/by_version/{version}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting transaction version {version}: {str(e)}")
            return None
    
    def get_ledger_info(self):
        """Get ledger information."""
        try:
            response = requests.get(self.node_url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting ledger info: {str(e)}")
            return None
    
    def process_event(self, event):
        """Process a blockchain event and notify handlers."""
        try:
            # Call all registered event handlers
            for handler in self.event_handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
    
    async def websocket_listener(self):
        """Listen for events via WebSocket connection."""
        while self.running:
            try:
                logger.info(f"Connecting to WebSocket at {self.ws_url}")
                async with websockets.connect(self.ws_url) as websocket:
                    # Subscribe to events for each subscription
                    for sub in self.subscriptions:
                        if sub["type"] == "events" and sub["account"] and sub["event_handle"] and sub["field_name"]:
                            await websocket.send(json.dumps({
                                "method": "events.subscribe",
                                "params": [
                                    sub["account"],
                                    sub["event_handle"],
                                    sub["field_name"]
                                ],
                                "id": 1
                            }))
                            logger.info(f"Subscribed to events: {sub['account']}/{sub['event_handle']}/{sub['field_name']}")
                        elif sub["type"] == "transactions":
                            await websocket.send(json.dumps({
                                "method": "transactions.subscribe",
                                "params": [],
                                "id": 2
                            }))
                            logger.info("Subscribed to all transactions")
                    
                    # Process incoming events
                    self.websocket_available = True
                    while self.running:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=30)
                            event_data = json.loads(response)
                            
                            # Check if it's a subscription confirmation
                            if "id" in event_data and "result" in event_data:
                                logger.info(f"Subscription confirmed: {event_data}")
                                continue
                                
                            # Process the event
                            logger.debug(f"Received event via WebSocket: {event_data}")
                            self.process_event(event_data)
                            
                        except asyncio.TimeoutError:
                            # Send a ping to keep the connection alive
                            try:
                                await websocket.send(json.dumps({"method": "ping", "id": 9999}))
                            except:
                                # Connection might be closed, break to reconnect
                                break
                        except Exception as e:
                            logger.error(f"Error processing WebSocket message: {str(e)}")
                            # If we encounter an error, break to reconnect
                            break
            
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                self.websocket_available = False
                
            # Wait before reconnecting
            logger.info(f"Reconnecting WebSocket in {self.reconnect_delay} seconds...")
            await asyncio.sleep(self.reconnect_delay)
    
    async def rest_api_poller(self):
        """Poll for events using REST API as fallback."""
        while self.running:
            try:
                # Only use REST API if WebSocket is not available
                if not self.websocket_available:
                    logger.info("Using REST API fallback for event polling")
                    
                    current_version = self.get_latest_version()
                    last_version = self.get_last_processed_version()
                    
                    if current_version > last_version:
                        logger.info(f"Fetching events from version {last_version} to {current_version}")
                        
                        # Process each subscription
                        for sub in self.subscriptions:
                            try:
                                if sub["type"] == "events" and sub["account"] and sub["event_handle"] and sub["field_name"]:
                                    events = self.get_events_by_event_handle(
                                        sub["account"], 
                                        sub["event_handle"], 
                                        sub["field_name"],
                                        start=last_version
                                    )
                                    
                                    for event in events:
                                        self.process_event(event)
                                        
                                elif sub["type"] == "transactions":
                                    transactions = self.get_transactions(start_version=last_version)
                                    
                                    for txn in transactions:
                                        self.process_event({"type": "transaction", "data": txn})
                            
                            except Exception as e:
                                logger.error(f"Error processing subscription {sub}: {str(e)}")
                        
                        # Update last processed version
                        self.save_last_processed_version(current_version)
                
                # Wait before next poll
                await asyncio.sleep(self.fallback_poll_interval)
            
            except Exception as e:
                logger.error(f"Error in REST API poller: {str(e)}")
                await asyncio.sleep(self.fallback_poll_interval)
    
    async def start(self):
        """Start the event monitoring."""
        self.running = True
        
        # Start both WebSocket listener and REST API poller
        # The poller will only actively fetch if WebSocket is unavailable
        await asyncio.gather(
            self.websocket_listener(),
            self.rest_api_poller()
        )
    
    def stop(self):
        """Stop the event monitoring."""
        self.running = False
        logger.info("Stopping Aptos event monitoring")

# Example usage
async def example():
    client = AptosWebSocketClient()
    
    # Register event handler
    client.register_event_handler(lambda event: print(f"Event received: {json.dumps(event, indent=2)}"))
    
    # Subscribe to events
    client.subscribe_to_events(
        "events",
        "0x1",
        "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>",
        "withdraw_events"
    )
    
    # Start monitoring
    await client.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example())
