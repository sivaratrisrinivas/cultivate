#!/usr/bin/env python3
"""
Improved Aptos Events Fetcher
Fetches real-time events from Aptos blockchain using the transaction history approach
which is more reliable than direct event handle access.
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
            # Start from a recent version to avoid processing the entire history
            return self.get_latest_version() - 100
            
    def save_last_processed_version(self, version):
        with open(self.last_version_file, "w") as f:
            f.write(str(version))
    
    def get_latest_version(self):
        response = requests.get(f"{self.node_url}")
        return int(response.json().get("ledger_version", "0"))
    
    def fetch_transaction(self, version):
        """Fetch a specific transaction by version."""
        url = f"{self.node_url}/transactions/by_version/{version}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    
    def fetch_transactions(self, start_version, limit=20):
        """Fetch a batch of transactions starting from a specific version."""
        url = f"{self.node_url}/transactions?start={start_version}&limit={limit}"
        print(f"Fetching transactions from: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        print(f"Error fetching transactions: {response.status_code} - {response.text}")
        return []
    
    def analyze_transaction(self, tx):
        """Analyze a transaction for interesting events."""
        result = {
            "hash": tx.get("hash", "Unknown"),
            "version": tx.get("version", "Unknown"),
            "sender": tx.get("sender", "Unknown"),
            "type": tx.get("type", "Unknown"),
            "timestamp": tx.get("timestamp", "Unknown"),
            "events": [],
            "is_interesting": False
        }
        
        # Extract events
        events = tx.get("events", [])
        if events:
            for event in events:
                event_type = event.get("type", "Unknown")
                
                # Check if this is an interesting event
                is_interesting = False
                importance = 0.5  # Default importance
                
                # Coin/token transfers
                if "coin::deposit" in event_type.lower() or "coin::withdraw" in event_type.lower():
                    is_interesting = True
                    importance = 0.6
                    
                    # Check amount for high-value transfers
                    amount = event.get("data", {}).get("amount", 0)
                    try:
                        if int(amount) > 1000000000:  # 1000 APT (assuming 8 decimals)
                            importance = 0.8
                    except:
                        pass
                
                # NFT events
                elif "nft" in event_type.lower() or "token" in event_type.lower():
                    is_interesting = True
                    importance = 0.7
                
                # Governance events
                elif "governance" in event_type.lower() or "voting" in event_type.lower():
                    is_interesting = True
                    importance = 0.9
                
                # Staking events
                elif "stake" in event_type.lower():
                    is_interesting = True
                    importance = 0.75
                
                # Add event to result
                event_info = {
                    "type": event_type,
                    "data": event.get("data", {}),
                    "is_interesting": is_interesting,
                    "importance": importance
                }
                
                result["events"].append(event_info)
                
                # Mark transaction as interesting if it has at least one interesting event
                if is_interesting:
                    result["is_interesting"] = True
        
        return result
    
    def poll_events(self, polling_interval=10, max_iterations=3, batch_size=20):
        """
        Poll for events by analyzing transactions.
        
        Args:
            polling_interval: Time between polls in seconds
            max_iterations: Maximum number of polling iterations (for testing)
            batch_size: Number of transactions to fetch in each batch
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
                
                # Calculate how many batches we need
                versions_to_process = min(current_version - last_version, 100)  # Limit to 100 versions at a time
                batches_needed = (versions_to_process + batch_size - 1) // batch_size
                
                print(f"Processing {versions_to_process} versions in {batches_needed} batches")
                
                interesting_txs = []
                processed_versions = 0
                
                # Process in batches
                for batch in range(batches_needed):
                    start_version = last_version + (batch * batch_size)
                    
                    # Fetch transactions
                    transactions = self.fetch_transactions(start_version, limit=batch_size)
                    processed_versions += len(transactions)
                    
                    # Analyze transactions
                    for tx in transactions:
                        tx_analysis = self.analyze_transaction(tx)
                        if tx_analysis["is_interesting"]:
                            interesting_txs.append(tx_analysis)
                
                # Report results
                print(f"\nProcessed {processed_versions} transactions")
                print(f"Found {len(interesting_txs)} interesting transactions with events")
                
                # Display interesting transactions
                if interesting_txs:
                    print("\n----- Interesting Transactions -----")
                    for i, tx in enumerate(interesting_txs[:5]):  # Show up to 5 interesting transactions
                        print(f"\nTransaction {i+1}: {tx['hash']}")
                        print(f"  Type: {tx['type']}")
                        print(f"  Sender: {tx['sender']}")
                        print(f"  Version: {tx['version']}")
                        print(f"  Timestamp: {tx['timestamp']}")
                        print(f"  Interesting Events: {sum(1 for e in tx['events'] if e['is_interesting'])}")
                        
                        # Show interesting events
                        for j, event in enumerate([e for e in tx['events'] if e['is_interesting']][:3]):  # Show up to 3 interesting events
                            print(f"    Event {j+1}: {event['type']} (Importance: {event['importance']})")
                            print(f"      Data: {json.dumps(event['data'], indent=2)[:150]}...")  # Truncate long data
                
                # Update last processed version
                new_last_version = last_version + processed_versions
                self.save_last_processed_version(new_last_version)
                print(f"\nUpdated last processed version to {new_last_version}")
            else:
                print("No new ledger versions since last check")
            
            if iteration < max_iterations:
                print(f"\nSleeping for {polling_interval} seconds...")
                time.sleep(polling_interval)

def main():
    """Main function to fetch Aptos events."""
    print("=" * 80)
    print("IMPROVED APTOS BLOCKCHAIN EVENTS FETCHER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Initialize poller
    poller = AptosEventsPoller()
    
    # Poll for events
    try:
        poller.poll_events(polling_interval=10, max_iterations=3, batch_size=20)
    except KeyboardInterrupt:
        print("\nPolling stopped by user")
    except Exception as e:
        print(f"\nError during polling: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Aptos events fetching completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
