#!/usr/bin/env python3
"""
Direct Aptos Events Fetcher
Fetches real-time events from Aptos blockchain using direct REST API calls
without relying on the existing blockchain module.
"""

import requests
import json
import time
import os
from datetime import datetime

class AptosEventsPoller:
    def __init__(self, node_url="https://fullnode.mainnet.aptoslabs.com/v1"):
        self.node_url = node_url
        self.last_version_file = "last_version.txt"
        
    def get_last_processed_version(self):
        try:
            with open(self.last_version_file, "r") as f:
                return int(f.read().strip())
        except:
            return 0
            
    def save_last_processed_version(self, version):
        with open(self.last_version_file, "w") as f:
            f.write(str(version))
    
    def get_latest_version(self):
        response = requests.get(f"{self.node_url}")
        return int(response.json().get("ledger_version", "0"))
    
    def fetch_events_by_handle(self, address, event_handle, field_name, limit=10):
        url = f"{self.node_url}/accounts/{address}/events/{event_handle}/{field_name}?limit={limit}"
        print(f"Fetching events from: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        print(f"Error fetching events: {response.status_code} - {response.text}")
        return []
    
    def fetch_transactions(self, start_version, limit=100):
        url = f"{self.node_url}/transactions?start={start_version}&limit={limit}"
        print(f"Fetching transactions from: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        print(f"Error fetching transactions: {response.status_code} - {response.text}")
        return []
    
    def poll_events(self, accounts_to_monitor, polling_interval=60, max_iterations=3):
        """
        Poll for events from specified accounts.
        
        Args:
            accounts_to_monitor: List of dictionaries with account details
            polling_interval: Time between polls in seconds
            max_iterations: Maximum number of polling iterations (for testing)
        """
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n===== Polling Iteration {iteration}/{max_iterations} =====")
            
            current_version = self.get_latest_version()
            last_version = self.get_last_processed_version()
            
            print(f"Current ledger version: {current_version}")
            print(f"Last processed version: {last_version}")
            
            if current_version > last_version:
                print(f"Fetching events from version {last_version} to {current_version}")
                
                # Approach 1: Fetch transactions and look for events
                transactions = self.fetch_transactions(last_version, limit=20)
                print(f"Fetched {len(transactions)} transactions")
                
                if transactions:
                    print("\n----- Transaction Events -----")
                    for tx in transactions[:3]:  # Show details for first 3 transactions
                        print(f"\nTransaction: {tx.get('hash', 'Unknown hash')}")
                        print(f"  Type: {tx.get('type', 'Unknown type')}")
                        print(f"  Sender: {tx.get('sender', 'Unknown sender')}")
                        print(f"  Version: {tx.get('version', 'Unknown version')}")
                        
                        # Check for events
                        events = tx.get('events', [])
                        if events:
                            print(f"  Events: {len(events)} found")
                            for event in events[:2]:  # Show first 2 events
                                print(f"    Event Type: {event.get('type', 'Unknown type')}")
                                print(f"    Event Data: {json.dumps(event.get('data', {}), indent=2)[:150]}...")
                
                # Approach 2: Directly fetch events from accounts of interest
                print("\n----- Account Events -----")
                all_events_count = 0
                
                for account in accounts_to_monitor:
                    events = self.fetch_events_by_handle(
                        account["address"],
                        account["handle"],
                        account["field"],
                        limit=5  # Limit to 5 events per account
                    )
                    
                    if events:
                        all_events_count += len(events)
                        print(f"\nFound {len(events)} events for {account['name']}")
                        
                        # Display sample events
                        for i, event in enumerate(events[:2]):  # Show first 2 events
                            print(f"\n  Event {i+1}:")
                            print(f"    Version: {event.get('version', 'Unknown')}")
                            print(f"    Sequence Number: {event.get('sequence_number', 'Unknown')}")
                            print(f"    Data: {json.dumps(event.get('data', {}), indent=2)[:150]}...")
                    else:
                        print(f"\nNo events found for {account['name']}")
                
                print(f"\nTotal events found across all accounts: {all_events_count}")
                
                # Update last processed version
                self.save_last_processed_version(current_version)
            else:
                print("No new ledger versions since last check")
            
            if iteration < max_iterations:
                print(f"\nSleeping for {polling_interval} seconds...")
                time.sleep(polling_interval)

def main():
    """Main function to fetch Aptos events."""
    print("=" * 80)
    print("APTOS BLOCKCHAIN EVENTS FETCHER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Accounts and event handles to monitor
    accounts_to_monitor = [
        # Binance
        {
            "name": "Binance",
            "address": "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92",
            "handle": "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>",
            "field": "withdraw_events"
        },
        # Coinbase
        {
            "name": "Coinbase",
            "address": "0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4",
            "handle": "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>",
            "field": "deposit_events"
        },
        # Topaz NFT marketplace
        {
            "name": "Topaz NFT Marketplace",
            "address": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",
            "handle": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2::marketplace::ListingEvents",
            "field": "listing_events"
        },
        # Aptos Foundation
        {
            "name": "Aptos Foundation",
            "address": "0x1",
            "handle": "0x1::stake::ValidatorPerformance",
            "field": "create_proposal_events"
        }
    ]
    
    # Initialize poller
    poller = AptosEventsPoller()
    
    # Poll for events
    try:
        poller.poll_events(accounts_to_monitor, polling_interval=10, max_iterations=3)
    except KeyboardInterrupt:
        print("\nPolling stopped by user")
    except Exception as e:
        print(f"\nError during polling: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Aptos events fetching completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
