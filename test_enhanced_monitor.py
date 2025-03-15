#!/usr/bin/env python3
"""
Enhanced Blockchain Monitor Test Script
This script demonstrates the enhanced blockchain monitoring features:
1. Account validation
2. Dynamic event handle discovery
3. Event correlation
4. Discord notifications
"""

import asyncio
import logging
import argparse
import json
import os
from datetime import datetime
from tabulate import tabulate
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import Config
from modules.blockchain import BlockchainMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/enhanced_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Rich console for pretty output
console = Console()

def format_event_for_display(event):
    """Format a blockchain event for display."""
    event_type = event.event_type.upper()
    importance = event.importance_score
    category = event.category.upper()
    
    # Determine color based on importance
    if importance >= 0.8:
        color = "bright_red"
    elif importance >= 0.7:
        color = "yellow"
    elif importance >= 0.6:
        color = "green"
    else:
        color = "blue"
    
    # Format event data
    data_str = ""
    for key, value in event.data.items():
        if key == "transaction_hash" and value:
            data_str += f"\n  [link=https://explorer.aptoslabs.com/txn/{value}]Transaction[/link]: {value[:10]}...{value[-10:]}"
        elif key == "amount" and value:
            try:
                formatted_amount = "{:,}".format(int(value))
                data_str += f"\n  Amount: {formatted_amount}"
            except (ValueError, TypeError):
                data_str += f"\n  {key.capitalize()}: {value}"
        elif key == "event_subtype" and value:
            data_str += f"\n  Type: {value.upper()}"
        elif key == "sender" and value:
            data_str += f"\n  Sender: {value[:10]}...{value[-10:]}"
        elif key == "receiver" and value:
            data_str += f"\n  Receiver: {value[:10]}...{value[-10:]}"
        else:
            # Skip internal fields or empty values
            if not value or key.startswith("_"):
                continue
            data_str += f"\n  {key.capitalize()}: {value}"
    
    # Format timestamp
    try:
        timestamp = datetime.fromisoformat(event.timestamp)
        formatted_time = timestamp.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        formatted_time = event.timestamp
    
    # Return formatted string with color
    return f"[bold {color}]{event_type}[/bold {color}] ({category}) - Score: {importance:.2f} - {formatted_time}{data_str}"

async def main(duration, interval):
    """Run the enhanced blockchain monitor for a specified duration."""
    logger.info(f"Starting enhanced blockchain monitor")
    logger.info(f"Monitoring events for {duration} seconds with {interval} second intervals")
    
    # Initialize blockchain monitor
    config = Config()
    monitor = BlockchainMonitor(config)
    
    # First, validate accounts and discover event handles
    console.print(Panel.fit("Validating accounts of interest...", title="Account Validation"))
    valid_accounts = await monitor.validate_accounts()
    
    # Display validated accounts
    account_table = Table(title="Validated Accounts")
    account_table.add_column("Account Address", style="cyan")
    account_table.add_column("Status", style="green")
    
    for account in monitor.accounts_of_interest:
        if account in monitor.validated_accounts:
            account_table.add_row(account, "Valid")
        else:
            account_table.add_row(account, "Invalid")
    
    console.print(account_table)
    
    # Discover event handles
    console.print(Panel.fit("Discovering event handles...", title="Event Handle Discovery"))
    new_handles = await monitor.discover_event_handles()
    
    # Display discovered handles
    handle_table = Table(title="Discovered Event Handles")
    handle_table.add_column("Account", style="cyan")
    handle_table.add_column("Creation Number", style="magenta")
    handle_table.add_column("Field Name", style="green")
    handle_table.add_column("Resource Type", style="yellow")
    
    for handle in new_handles:
        handle_table.add_row(
            handle["account"], 
            handle["creation_number"], 
            handle["field_name"],
            handle.get("resource_type", "N/A")
        )
    
    console.print(handle_table)
    
    # Start monitoring
    console.print(Panel.fit(f"Starting event monitoring for {duration} seconds...", title="Event Monitoring"))
    
    end_time = asyncio.get_event_loop().time() + duration
    iteration = 1
    
    all_events = []
    all_correlated_events = []
    
    while asyncio.get_event_loop().time() < end_time:
        logger.info(f"Iteration {iteration}: Fetching events...")
        console.print(f"[bold blue]Iteration {iteration}[/bold blue]: Fetching events...")
        
        # Fetch events
        events = await monitor.fetch_events_async()
        all_events.extend(events)
        
        # Get correlated events
        correlated_events = monitor.correlated_events
        all_correlated_events.extend(correlated_events)
        
        # Display events
        if events:
            console.print(f"\n[bold green]Found {len(events)} significant events:[/bold green]")
            for event in events:
                console.print(format_event_for_display(event))
        else:
            console.print("[yellow]No significant events found in this iteration[/yellow]")
        
        # Display correlated events
        if correlated_events:
            console.print(f"\n[bold magenta]Found {len(correlated_events)} correlated event groups:[/bold magenta]")
            for i, group in enumerate(correlated_events):
                console.print(f"[bold]Group {i+1}:[/bold]")
                for event in group:
                    console.print(f"  {format_event_for_display(event)}")
        
        # Wait for next iteration
        if asyncio.get_event_loop().time() < end_time:
            await asyncio.sleep(interval)
            iteration += 1
    
    # Save all events to a file
    if all_events:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/enhanced_events_{timestamp}.json"
        os.makedirs("data", exist_ok=True)
        
        with open(filename, "w") as f:
            json.dump([e.to_dict() for e in all_events], f, indent=2)
        
        logger.info(f"Saved events to {filename}")
        console.print(f"[green]Events saved to {filename}[/green]")
    
    # Save correlated events to a file
    if all_correlated_events:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/correlated_events_{timestamp}.json"
        
        # We need to convert the event objects to dictionaries
        serializable_correlated = []
        for event in all_correlated_events:
            serializable_event = event.copy()
            if "from_event" in serializable_event:
                serializable_event["from_event"] = serializable_event["from_event"].to_dict()
            if "to_event" in serializable_event:
                serializable_event["to_event"] = serializable_event["to_event"].to_dict()
            if "listing_event" in serializable_event:
                serializable_event["listing_event"] = serializable_event["listing_event"].to_dict()
            if "sale_event" in serializable_event:
                serializable_event["sale_event"] = serializable_event["sale_event"].to_dict()
            serializable_correlated.append(serializable_event)
        
        with open(filename, "w") as f:
            json.dump(serializable_correlated, f, indent=2)
        
        logger.info(f"Saved correlated events to {filename}")
        console.print(f"[green]Correlated events saved to {filename}[/green]")
    
    # Display all events at the end
    if all_events:
        console.print(f"\n[bold cyan]Summary of all {len(all_events)} events:[/bold cyan]")
        
        # Group by category
        events_by_category = {}
        for event in all_events:
            category = event.category
            if category not in events_by_category:
                events_by_category[category] = []
            events_by_category[category].append(event)
        
        # Display by category
        for category, events in events_by_category.items():
            console.print(f"\n[bold]Category: {category.upper()} ({len(events)} events)[/bold]")
            # Sort by importance
            events.sort(key=lambda x: x.importance_score, reverse=True)
            # Display top 5 most important events in this category
            for event in events[:5]:
                console.print(format_event_for_display(event))
            if len(events) > 5:
                console.print(f"[dim]...and {len(events) - 5} more events in this category[/dim]")
    
    # Final summary
    console.print(Panel.fit("Enhanced Blockchain Monitor Complete", title="Summary"))
    console.print(f"[bold]Total Events Captured:[/bold] {len(all_events)}")
    console.print(f"[bold]Total Correlated Events:[/bold] {len(all_correlated_events)}")
    console.print(f"[bold]Total Iterations:[/bold] {iteration}")
    
    # Stop the monitor
    monitor.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Blockchain Monitor")
    parser.add_argument("duration", type=int, help="Duration to run the monitor in seconds")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds")
    args = parser.parse_args()
    
    asyncio.run(main(args.duration, args.interval))
