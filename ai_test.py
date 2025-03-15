#!/usr/bin/env python3
"""
Comprehensive test script for the AI module.
This script tests all functionality of the AI module, including:
1. Direct X.AI API integration
2. Content generation from blockchain events
3. Meme generation
4. Question answering
"""

import os
import json
import requests
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
logger = get_logger("ai_test")
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
            importance_score=0.9
        ),
        BlockchainEvent(
            "contract_event", 
            "deployment", 
            {
                "blockchain": "Aptos",
                "address": "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",
                "module_name": "marketplace",
                "event_subtype": "contract_deployed"
            },
            importance_score=0.75
        ),
        BlockchainEvent(
            "governance_event", 
            "proposal", 
            {
                "blockchain": "Aptos",
                "proposal_id": "AIP-12345",
                "title": "Increase staking rewards",
                "proposer": "0x1",
                "event_subtype": "proposal_created"
            },
            importance_score=0.8
        )
    ]

async def fetch_real_events(config):
    """Fetch real events from the blockchain."""
    console.print(Panel("Fetching Real Blockchain Events", title="Blockchain Monitor"))
    
    try:
        # Initialize blockchain monitor
        monitor = BlockchainMonitor(config)
        
        # Fetch events
        events = monitor.fetch_events()
        
        if events:
            console.print(f"✅ Successfully fetched {len(events)} real events")
            
            # Display sample events
            table = Table(title="Sample Blockchain Events")
            table.add_column("Type", style="cyan")
            table.add_column("Category", style="green")
            table.add_column("Importance", style="yellow")
            table.add_column("Data", style="white")
            
            for event in events[:3]:  # Show up to 3 events
                table.add_row(
                    event.event_type,
                    event.category,
                    str(event.importance_score),
                    str(event.data)[:50] + "..." if len(str(event.data)) > 50 else str(event.data)
                )
            
            console.print(table)
            return events
        else:
            console.print("❌ No real events fetched")
            return []
    except Exception as e:
        console.print(f"❌ Error fetching real events: {str(e)}")
        return []

def test_xai_api_directly():
    """Test X.AI API directly with a simple request."""
    console.print(Panel("Testing X.AI API Directly", title="API Test"))
    
    # Get API key from config
    config = Config()
    api_key = config.AI["API_KEY"]
    api_url = config.AI["API_URL"]
    model = config.AI["MODEL"]
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a test assistant."
                },
                {
                    "role": "user",
                    "content": "Testing. Just say hi and hello world and nothing else."
                }
            ],
            "model": model,
            "temperature": 0.7
        }
        
        console.print("Sending test request to X.AI API...")
        response = requests.post(
            f"{api_url}/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            console.print("✅ API test successful")
            console.print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            console.print(f"❌ API test failed with status code {response.status_code}")
            console.print(f"Error: {response.text}")
            return False
    except Exception as e:
        console.print(f"❌ API test failed with exception: {str(e)}")
        return False

def test_ai_content_generation(ai_module, events):
    """Test AI content generation with blockchain events."""
    console.print(Panel("Testing AI Content Generation", title="Content Generation"))
    
    for i, event in enumerate(events[:2]):  # Test with first 2 events
        console.print(f"\n[bold cyan]Event {i+1}:[/bold cyan] {event.event_type} ({event.category})")
        console.print(f"Data: {json.dumps(event.data, indent=2)}")
        
        # Generate social post
        try:
            post = ai_module.compose_social_post(event)
            console.print(Panel(post, title=f"Generated Social Post for {event.event_type}", border_style="green"))
        except Exception as e:
            console.print(f"❌ Error generating social post: {str(e)}")

def test_ai_meme_generation(ai_module, events):
    """Test AI meme generation with blockchain events."""
    console.print(Panel("Testing AI Meme Generation", title="Meme Generation"))
    
    for i, event in enumerate(events[:1]):  # Test with first event only
        console.print(f"\n[bold cyan]Event {i+1}:[/bold cyan] {event.event_type} ({event.category})")
        
        # Generate meme
        try:
            meme_path = ai_module.create_meme(event)
            if meme_path and os.path.exists(meme_path):
                console.print(f"✅ Meme generated successfully at: {meme_path}")
            else:
                console.print("❌ Meme generation failed or file not found")
        except Exception as e:
            console.print(f"❌ Error generating meme: {str(e)}")

def test_ai_qa(ai_module):
    """Test AI Q&A functionality."""
    console.print(Panel("Testing AI Q&A Functionality", title="Question Answering"))
    
    test_questions = [
        "What is Aptos blockchain?",
        "How does staking work on Aptos?",
        "What are the main features of Move language?"
    ]
    
    for i, question in enumerate(test_questions):
        console.print(f"\n[bold cyan]Question {i+1}:[/bold cyan] {question}")
        
        # Get answer
        try:
            answer = ai_module.answer_question(question)
            console.print(Panel(answer, title=f"Answer to Question {i+1}", border_style="green"))
        except Exception as e:
            console.print(f"❌ Error answering question: {str(e)}")

async def main():
    """Main function to run tests."""
    console.print(Panel("AI Module Comprehensive Test Suite", title="Test Started", subtitle=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    
    # Load configuration
    config = Config()
    
    # Initialize AI module
    ai_module = AIModule(config)
    
    # Test X.AI API directly
    api_working = test_xai_api_directly()
    
    if not api_working:
        console.print("[bold red]Warning: X.AI API test failed. Some tests may not work correctly.[/bold red]")
    
    # Load test events
    events = load_test_events()
    console.print(f"Loaded {len(events)} test events")
    
    # Try to fetch real events
    real_events = await fetch_real_events(config)
    
    # Use real events if available, otherwise use test events
    if real_events:
        console.print("Using real blockchain events for testing")
        test_events = real_events
    else:
        console.print("Using sample blockchain events for testing")
        test_events = events
    
    # Test AI content generation
    test_ai_content_generation(ai_module, test_events)
    
    # Test AI meme generation
    test_ai_meme_generation(ai_module, test_events)
    
    # Test AI Q&A
    test_ai_qa(ai_module)
    
    console.print(Panel("AI Module Test Suite Completed", title="Test Completed", subtitle=f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[bold red]Test interrupted by user[/bold red]")
        exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Test failed with exception: {str(e)}[/bold red]")
        exit(2)
