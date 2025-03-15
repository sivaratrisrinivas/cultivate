#!/usr/bin/env python3
"""
Test script for the X.AI API integration with the AI module.
This script tests the AI module's ability to process blockchain data
and generate content using the X.AI API.
"""

import os
import json
import asyncio
import requests
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

# X.AI API credentials
XAI_API_KEY = "xai-pgMzqd2Oi0PFYOwPlaJ3bnSeqct4dWfFpAWJZ0KtKwiAvHyfbYvi5CujBikjtICZEYD8FeemS2GwXWXR"
XAI_API_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-2-latest"

def test_xai_api_directly():
    """Test X.AI API directly with a simple request."""
    console.print(Panel("Testing X.AI API Directly", title="API Test"))
    
    try:
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
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
            "model": XAI_MODEL,
            "stream": False,
            "temperature": 0
        }
        
        response = requests.post(
            f"{XAI_API_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract the generated text
        generated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        console.print(Panel(f"[green]API Response:[/green] {generated_text}", title="Direct API Test Result"))
        return True
        
    except Exception as e:
        logger.error(f"Error testing X.AI API directly: {str(e)}")
        console.print(f"[red]Error testing X.AI API directly: {str(e)}[/red]")
        return False

def load_sample_events():
    """Load sample blockchain events for testing."""
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

def test_ai_module_with_xai_api(config):
    """Test AI module with X.AI API using sample blockchain events."""
    console.print(Panel("Testing AI Module with X.AI API", title="Module Test"))
    
    # Update config with X.AI API credentials
    config.AI["API_KEY"] = XAI_API_KEY
    config.AI["API_URL"] = XAI_API_URL
    config.AI["MODEL"] = XAI_MODEL
    
    # Initialize AI module with updated config
    ai_module = AIModule(config)
    
    # Load sample events
    events = load_sample_events()
    console.print(f"[yellow]Loaded {len(events)} sample events for testing[/yellow]")
    
    # Create a table for results
    table = Table(title="AI Generated Content with X.AI API")
    table.add_column("Event Type", style="cyan")
    table.add_column("Importance", style="magenta")
    table.add_column("Generated Content", style="green", width=60)
    
    # Process each event
    for event in events:
        try:
            # Generate social media post
            post = ai_module.generate_post(event)
            
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
    
    # Test Q&A functionality
    console.print(Panel("Testing AI Q&A with X.AI API", title="Q&A Test"))
    
    questions = [
        "What is Aptos blockchain?",
        "How many transactions per second can Aptos handle?",
        "What is the Move language?",
        "What was the latest significant event on Aptos?"
    ]
    
    # Create a table for Q&A results
    qa_table = Table(title="AI Q&A Results with X.AI API")
    qa_table.add_column("Question", style="cyan")
    qa_table.add_column("Answer", style="green", width=60)
    qa_table.add_column("Confidence", style="yellow")
    
    for question in questions:
        try:
            # Get answer
            result = ai_module.get_answer(question)
            
            # Add to table
            qa_table.add_row(
                question,
                result["answer"],
                f"{result['confidence']:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Error getting answer for question '{question}': {str(e)}")
            console.print(f"[red]Error getting answer for question '{question}': {str(e)}[/red]")
    
    # Display Q&A results
    console.print(qa_table)

def main():
    """Main function to run tests."""
    console.print(Panel("Starting X.AI API Integration Tests", title="Test Suite"))
    
    # Test X.AI API directly
    api_test_success = test_xai_api_directly()
    
    if api_test_success:
        # Load configuration
        config = Config()
        
        # Test AI module with X.AI API
        test_ai_module_with_xai_api(config)
    else:
        console.print("[red]Skipping AI module tests due to API test failure[/red]")
    
    console.print(Panel("X.AI API Integration Tests Complete", title="Test Results"))

if __name__ == "__main__":
    main()
