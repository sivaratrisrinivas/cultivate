#!/usr/bin/env python3
# test_specific_events.py
import os
import sys
import asyncio
import time
import json
from datetime import datetime
from tabulate import tabulate
from config import Config
from modules.blockchain import BlockchainMonitor, BlockchainEvent
from utils.logger import get_logger

# Set up logging
logger = get_logger("test_specific_events")

class SpecificEventMonitor:
    """Monitor specific high-value events from the Aptos blockchain."""
    
    def __init__(self):
        """Initialize the monitor."""
        # Load configuration
        self.config = Config()
        
        # Initialize blockchain monitor
        self.blockchain_monitor = BlockchainMonitor(self.config)
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Event categories to track
        self.event_categories = {
            "nft": ["nft_collection_created", "nft_mint", "nft_marketplace", "nft_event"],
            "token": ["token_event"],
            "contract": ["contract_event"],
            "governance": ["governance_event"],
            "transaction": ["significant_transaction", "transaction_event"],
            "staking": ["staking_event"],
        }
        
        # Track events by category
        self.events_by_category = {category: [] for category in self.event_categories}
        
        # Track events by account
        self.events_by_account = {}
        
        # Track high importance events
        self.high_importance_events = []
    
    def categorize_event(self, event):
        """Categorize an event based on its type."""
        for category, event_types in self.event_categories.items():
            if event.event_type in event_types:
                return category
        return "other"
    
    def track_event_by_account(self, event, sender):
        """Track events by account."""
        if sender not in self.events_by_account:
            self.events_by_account[sender] = []
        self.events_by_account[sender].append(event)
    
    def print_event_summary(self):
        """Print a summary of tracked events."""
        print("\n=== Event Summary by Category ===")
        rows = []
        for category, events in self.events_by_category.items():
            rows.append([category.upper(), len(events)])
        print(tabulate(rows, headers=["Category", "Count"], tablefmt="grid"))
        
        print("\n=== Top 5 High Importance Events ===")
        if self.high_importance_events:
            rows = []
            for event in self.high_importance_events[:5]:
                rows.append([
                    event.event_type,
                    event.importance_score,
                    event.timestamp,
                    json.dumps(event.data, indent=2)[:100] + "..." if len(json.dumps(event.data)) > 100 else json.dumps(event.data)
                ])
            print(tabulate(rows, headers=["Event Type", "Importance", "Timestamp", "Data Preview"], tablefmt="grid"))
        else:
            print("No high importance events found.")
        
        print("\n=== Events by Account of Interest ===")
        if self.events_by_account:
            rows = []
            for account, events in self.events_by_account.items():
                account_name = "Unknown"
                if account == "0x1":
                    account_name = "Aptos Foundation"
                elif account == "0x0108bc32f7de18a5f6e1e7d6ee7aff9f5fc858d0d87ac0da94dd8d2a5d267d6b":
                    account_name = "Aptos Labs"
                elif account == "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92":
                    account_name = "Binance"
                elif account == "0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4":
                    account_name = "Coinbase"
                elif account == "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2":
                    account_name = "Topaz Marketplace"
                
                rows.append([
                    account[:10] + "...",
                    account_name,
                    len(events),
                    ", ".join(set([e.event_type for e in events]))
                ])
            print(tabulate(rows, headers=["Account", "Name", "Event Count", "Event Types"], tablefmt="grid"))
        else:
            print("No events from accounts of interest found.")
    
    def save_events_to_file(self):
        """Save tracked events to a file for later analysis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/events_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_events": sum(len(events) for events in self.events_by_category.values()),
            "events_by_category": {
                category: [event.to_dict() for event in events]
                for category, events in self.events_by_category.items()
            },
            "high_importance_events": [event.to_dict() for event in self.high_importance_events],
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved events to {filename}")
        return filename
    
    async def monitor_events(self, duration_seconds=300, interval_seconds=30):
        """Monitor events for a specified duration."""
        logger.info(f"Monitoring events for {duration_seconds} seconds with {interval_seconds} second intervals")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        iteration = 1
        
        while time.time() < end_time:
            logger.info(f"Iteration {iteration}: Fetching events...")
            
            # Fetch events
            events = await self.blockchain_monitor.fetch_events_async()
            
            if events:
                logger.info(f"Found {len(events)} events in iteration {iteration}")
                
                # Process events
                for event in events:
                    # Categorize event
                    category = self.categorize_event(event)
                    if category != "other":
                        self.events_by_category[category].append(event)
                    
                    # Track high importance events
                    if event.importance_score >= 0.75:
                        self.high_importance_events.append(event)
                    
                    # Track events by account if transaction_hash is available
                    if "transaction_hash" in event.data:
                        # For demonstration, use a dummy sender
                        sender = event.data.get("sender", "unknown")
                        if sender in self.blockchain_monitor.accounts_of_interest:
                            self.track_event_by_account(event, sender)
                
                # Sort high importance events
                self.high_importance_events.sort(key=lambda x: x.importance_score, reverse=True)
                
                # Print current status
                print(f"\n--- Iteration {iteration} Results ---")
                print(f"Found {len(events)} events")
                print(f"High importance events: {len([e for e in events if e.importance_score >= 0.75])}")
                
                # Print event types distribution
                event_types = {}
                for event in events:
                    if event.event_type not in event_types:
                        event_types[event.event_type] = 0
                    event_types[event.event_type] += 1
                
                print("\nEvent Types Distribution:")
                for event_type, count in event_types.items():
                    print(f"  - {event_type}: {count}")
            else:
                logger.info(f"No events found in iteration {iteration}")
            
            # Wait for next interval if not the last iteration
            if time.time() + interval_seconds < end_time:
                iteration += 1
                await asyncio.sleep(interval_seconds)
            else:
                break
        
        # Print final summary
        self.print_event_summary()
        
        # Save events to file
        filename = self.save_events_to_file()
        print(f"\nEvents saved to {filename}")
        
        logger.info(f"Completed {iteration} iterations")
        return self.events_by_category, self.high_importance_events
    
    async def run(self, duration_seconds=300, interval_seconds=30):
        """Run the specific event monitor."""
        logger.info("Starting specific event monitor")
        
        try:
            await self.monitor_events(duration_seconds, interval_seconds)
            return 0
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
            self.print_event_summary()
            return 130
        except Exception as e:
            logger.error(f"Error monitoring events: {str(e)}")
            return 1

async def main():
    """Run the specific event monitor."""
    # Check for command line arguments
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            duration = 300
    else:
        duration = 300
    
    monitor = SpecificEventMonitor()
    return await monitor.run(duration_seconds=duration, interval_seconds=30)

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
