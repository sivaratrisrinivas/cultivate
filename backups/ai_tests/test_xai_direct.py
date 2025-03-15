#!/usr/bin/env python3
"""
Direct test of X.AI API with detailed logging to demonstrate
the API request and response process.
"""

import json
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("xai_api_test.log")
    ]
)

logger = logging.getLogger("xai_api_test")

# X.AI API credentials
XAI_API_KEY = "xai-pgMzqd2Oi0PFYOwPlaJ3bnSeqct4dWfFpAWJZ0KtKwiAvHyfbYvi5CujBikjtICZEYD8FeemS2GwXWXR"
XAI_API_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-2-latest"

def test_xai_api_with_blockchain_data():
    """Test X.AI API with blockchain data and log the entire process."""
    
    # Log start of test
    logger.info("Starting X.AI API test with blockchain data")
    
    # Create a sample blockchain event
    blockchain_event = {
        "event_type": "token_event",
        "category": "transfer",
        "data": {
            "blockchain": "Aptos",
            "amount": 1500000,
            "token_name": "APT",
            "from": "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92",
            "to": "0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4",
            "event_subtype": "large_transfer"
        },
        "timestamp": datetime.now().isoformat(),
        "importance_score": 0.95
    }
    
    # Log the event data
    logger.info(f"Blockchain event data: {json.dumps(blockchain_event, indent=2)}")
    
    # Create system prompt
    system_prompt = (
        "You are an AI assistant specialized in creating viral social media content "
        "about blockchain events, specifically for the Aptos blockchain. "
        "Your responses should be engaging, informative, and optimized for Twitter-style "
        "posts under 280 characters."
    )
    
    # Create user prompt based on event
    user_prompt = (
        f"Create a short, exciting tweet about {blockchain_event['data']['amount']} "
        f"{blockchain_event['data']['token_name']} just transferred on Aptos blockchain."
    )
    
    # Log the prompts
    logger.info(f"System prompt: {system_prompt}")
    logger.info(f"User prompt: {user_prompt}")
    
    try:
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare request data
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "model": XAI_MODEL,
            "stream": False,
            "temperature": 0.7
        }
        
        # Log request details (excluding API key)
        logger.info(f"Making API request to: {XAI_API_URL}/chat/completions")
        logger.info(f"Request data: {json.dumps(data, indent=2)}")
        
        # Make the API request
        logger.info("Sending request...")
        start_time = datetime.now()
        
        response = requests.post(
            f"{XAI_API_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30  # 30 second timeout
        )
        
        # Calculate response time
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        logger.info(f"Response received in {response_time:.2f} seconds")
        
        # Log response status
        logger.info(f"Response status code: {response.status_code}")
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        # Log response (excluding any sensitive data)
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response JSON: {json.dumps(result, indent=2)}")
        
        # Extract the generated text
        generated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        # Log the generated text
        logger.info(f"Generated content: {generated_text}")
        
        # Save the response to a file for reference
        with open("xai_api_response.json", "w") as f:
            json.dump(result, f, indent=2)
        logger.info("Saved full response to xai_api_response.json")
        
        # Print the generated content
        print("\n" + "="*80)
        print("BLOCKCHAIN EVENT:")
        print(f"Type: {blockchain_event['event_type']}")
        print(f"Amount: {blockchain_event['data']['amount']} {blockchain_event['data']['token_name']}")
        print("\nGENERATED CONTENT:")
        print(generated_text)
        print("="*80 + "\n")
        
        return True
        
    except requests.exceptions.Timeout:
        logger.error("API request timed out after 30 seconds")
        print("ERROR: API request timed out after 30 seconds")
        return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        print(f"ERROR: API request failed: {str(e)}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"ERROR: Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_xai_api_with_blockchain_data()
