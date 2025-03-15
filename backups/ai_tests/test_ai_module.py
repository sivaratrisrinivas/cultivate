#!/usr/bin/env python3
"""
Test script for the AI module to verify it can process blockchain data
and generate content based on blockchain events.
"""

import os
import json
import asyncio
from datetime import datetime
from modules.blockchain import BlockchainMonitor, BlockchainEvent
from modules.ai import AIModule
from config import Config
from utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Initialize logger and console
logger = get_logger(__name__)
console = Console()

def load_test_events():
    """Load test events from file or return sample events."""
    test_file = "data/test_events.json"
    
    if os.path.exists(test_file):
        try:
            with open(test_file, "r") as f:
                events_data = json.load(f)
                return [BlockchainEvent.from_dict(event) for event in events_data]
        except Exception as e:
            logger.error(f"Error loading test events: {str(e)}")
    
    # Return sample events if file doesn't exist or has errors
    return [
        BlockchainEvent(
            "nft_mint", 
            "nft", 
            {
                "blockchain": "Aptos",
                "collection_name": "Aptos Monkeys",
                "creator": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",
                "name": "Aptos Monkey #1234",
                "amount": 1,
                "type": "NFT_MINT"
            },
            importance_score=0.85
        ),
        BlockchainEvent(
            "token_event", 
            "transfer", 
            {
                "blockchain": "Aptos",
                "amount": 1500000,
                "token_name": "APT",
                "from": "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92",
                "to": "0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4",
                "event_subtype": "large_transfer"
            },
            importance_score=0.95
        ),
        BlockchainEvent(
            "contract_event", 
            "contract", 
            {
                "blockchain": "Aptos",
                "address": "0x0108bc32f7de18a5f6e1e7d6ee7aff9f5fc858d0d87ac0da94dd8d2a5d267d6b",
                "module_name": "marketplace",
                "event_subtype": "contract_deployed"
            },
            importance_score=0.9
        ),
        BlockchainEvent(
            "governance_event", 
            "governance", 
            {
                "blockchain": "Aptos",
                "proposal_id": 12,
                "votes": 1250000,
                "event_subtype": "governance"
            },
            importance_score=0.85
        )
    ]

async def fetch_real_events(config):
    """Fetch real events from the blockchain."""
    console.print(Panel("Fetching real blockchain events...", title="Blockchain Events"))
    
    try:
        # Initialize blockchain monitor
        monitor = BlockchainMonitor(config)
        
        # Validate accounts
        await monitor.validate_accounts()
        
        # Discover event handles
        await monitor.discover_event_handles()
        
        # Fetch events
        events = await monitor.fetch_events_async()
        
        if events:
            console.print(f"[green]Successfully fetched {len(events)} real events from blockchain[/green]")
            
            # Save events for future test runs
            try:
                with open("data/test_events.json", "w") as f:
                    json.dump([event.to_dict() for event in events], f, indent=2)
                console.print("[green]Saved events to data/test_events.json for future test runs[/green]")
            except Exception as e:
                logger.error(f"Error saving test events: {str(e)}")
                
            return events
        else:
            console.print("[yellow]No events found, using sample events instead[/yellow]")
            return load_test_events()
            
    except Exception as e:
        logger.error(f"Error fetching real events: {str(e)}")
        console.print(f"[red]Error fetching real events: {str(e)}[/red]")
        console.print("[yellow]Using sample events instead[/yellow]")
        return load_test_events()

def test_ai_content_generation(ai_module, events):
    """Test AI content generation with blockchain events."""
    console.print(Panel("Testing AI Content Generation", title="AI Module Test"))
    
    results = []
    
    # Create a table for results
    table = Table(title="AI Generated Content")
    table.add_column("Event Type", style="cyan")
    table.add_column("Importance", style="magenta")
    table.add_column("Generated Content", style="green", width=60)
    
    # Process each event
    for event in events[:5]:  # Limit to 5 events to avoid too much output
        try:
            # Generate social media post
            post = ai_module.generate_post(event)
            
            # Add to results
            results.append({
                "event_type": event.event_type,
                "importance": event.importance_score,
                "content": post["content"]
            })
            
            # Add to table
            table.add_row(
                event.event_type,
                f"{event.importance_score:.2f}",
                post["content"]
            )
            
        except Exception as e:
            logger.error(f"Error generating content for event {event.event_type}: {str(e)}")
            console.print(f"[red]Error generating content for event {event.event_type}: {str(e)}[/red]")
    
    # Display results
    console.print(table)
    
    return results

def test_ai_meme_generation(ai_module, events):
    """Test AI meme generation with blockchain events."""
    console.print(Panel("Testing AI Meme Generation", title="AI Module Test"))
    
    results = []
    
    # Create a table for results
    table = Table(title="AI Generated Memes")
    table.add_column("Event Type", style="cyan")
    table.add_column("Meme Text", style="green", width=60)
    table.add_column("Image Path", style="yellow")
    
    # Process each event
    for event in events[:2]:  # Limit to 2 events for meme generation
        try:
            # Generate meme
            meme = ai_module.generate_meme(event)
            
            # Add to results
            results.append({
                "event_type": event.event_type,
                "meme_text": meme["text"],
                "image_path": meme["image_path"]
            })
            
            # Add to table
            table.add_row(
                event.event_type,
                meme["text"],
                meme["image_path"]
            )
            
        except Exception as e:
            logger.error(f"Error generating meme for event {event.event_type}: {str(e)}")
            console.print(f"[red]Error generating meme for event {event.event_type}: {str(e)}[/red]")
    
    # Display results
    console.print(table)
    
    return results

def test_ai_qa(ai_module):
    """Test AI Q&A functionality."""
    console.print(Panel("Testing AI Q&A", title="AI Module Test"))
    
    questions = [
        "What is Aptos blockchain?",
        "How many transactions per second can Aptos handle?",
        "What is the Move language?",
        "What was the latest significant event on Aptos?"
    ]
    
    # Create a table for results
    table = Table(title="AI Q&A Results")
    table.add_column("Question", style="cyan")
    table.add_column("Answer", style="green", width=60)
    table.add_column("Confidence", style="yellow")
    
    for question in questions:
        try:
            # Get answer
            result = ai_module.get_answer(question)
            
            # Add to table
            table.add_row(
                question,
                result["answer"],
                f"{result['confidence']:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Error getting answer for question '{question}': {str(e)}")
            console.print(f"[red]Error getting answer for question '{question}': {str(e)}[/red]")
    
    # Display results
    console.print(table)

async def main():
    """Main function to run tests."""
    console.print(Panel("Starting AI Module Tests", title="Test Suite"))
    
    # Load configuration
    config = Config()
    
    # Initialize AI module
    ai_module = AIModule(config)
    
    # Fetch events (real or sample)
    use_real_events = True  # Set to False to use sample events
    
    if use_real_events:
        events = await fetch_real_events(config)
    else:
        events = load_test_events()
        console.print(f"[yellow]Using {len(events)} sample events[/yellow]")
    
    # Test content generation
    test_ai_content_generation(ai_module, events)
    
    # Test meme generation
    test_ai_meme_generation(ai_module, events)
    
    # Test Q&A
    test_ai_qa(ai_module)
    
    console.print(Panel("AI Module Tests Complete", title="Test Results"))

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
