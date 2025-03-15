#!/usr/bin/env python3
# test_api.py
import os
import sys
import json
import requests
import threading
import time
from config import Config
from modules.blockchain import BlockchainMonitor
from modules.ai import AIModule
from modules.discord_bot import DiscordBot
from api.app import create_app
from api.routes import initialize_modules
from utils.logger import get_logger

# Set up logging
logger = get_logger("test_api")

class APITester:
    """Test the API endpoints."""
    
    def __init__(self):
        """Initialize the API tester."""
        # Create necessary directories
        for dir_path in ['data', 'cache', 'logs', 'templates/memes']:
            os.makedirs(dir_path, exist_ok=True)
        
        # Load configuration
        self.config = Config()
        
        # Initialize modules
        self.blockchain_monitor = BlockchainMonitor(self.config)
        self.ai_module = AIModule(self.config)
        self.discord_bot = DiscordBot(self.config, self.ai_module)
        
        # Initialize API
        initialize_modules(self.blockchain_monitor, self.ai_module, self.discord_bot)
        self.app = create_app(self.config)
        
        # Set test port
        self.port = 5001
        self.base_url = f"http://localhost:{self.port}"
        
        # Start server thread
        self.server_thread = None
    
    def start_server(self):
        """Start the API server in a separate thread."""
        def run_server():
            self.app.run(host='localhost', port=self.port, debug=False)
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        logger.info(f"API server started on {self.base_url}")
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        logger.info("Testing root endpoint")
        
        try:
            response = requests.get(self.base_url)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Root endpoint response: {data}")
                
                if data.get("service") == "Aptos Social Media Manager" and data.get("status") == "operational":
                    logger.info("Root endpoint test PASSED")
                    return True
                else:
                    logger.error("Root endpoint returned unexpected data")
                    return False
            else:
                logger.error(f"Root endpoint returned status code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing root endpoint: {str(e)}")
            return False
    
    def test_status_endpoint(self):
        """Test the status endpoint."""
        logger.info("Testing status endpoint")
        
        try:
            response = requests.get(f"{self.base_url}/api/status")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Status endpoint response: {data}")
                
                if data.get("status") in ["operational", "degraded"] and "components" in data:
                    logger.info("Status endpoint test PASSED")
                    return True
                else:
                    logger.error("Status endpoint returned unexpected data")
                    return False
            else:
                logger.error(f"Status endpoint returned status code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing status endpoint: {str(e)}")
            return False
    
    def test_question_endpoint(self):
        """Test the question endpoint."""
        logger.info("Testing question endpoint")
        
        try:
            payload = {"question": "What is Aptos blockchain?"}
            response = requests.post(
                f"{self.base_url}/api/question",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Question endpoint response: {data}")
                
                if data.get("success") and data.get("answer") and "confidence" in data:
                    logger.info("Question endpoint test PASSED")
                    return True
                else:
                    logger.error("Question endpoint returned unexpected data")
                    return False
            else:
                logger.error(f"Question endpoint returned status code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing question endpoint: {str(e)}")
            return False
    
    def test_event_endpoint(self):
        """Test the event endpoint."""
        logger.info("Testing event endpoint")
        
        try:
            # Create test event
            payload = {
                "event_type": "nft_collection_created",
                "details": {
                    "collection_name": "Test Collection",
                    "creator": "0x12345",
                    "description": "A test NFT collection"
                },
                "importance_score": 0.9
            }
            
            response = requests.post(
                f"{self.base_url}/api/event",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Event endpoint response: {data}")
                
                if data.get("success") and data.get("content"):
                    logger.info("Event endpoint test PASSED")
                    return True
                else:
                    logger.error("Event endpoint returned unexpected data")
                    return False
            else:
                logger.error(f"Event endpoint returned status code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing event endpoint: {str(e)}")
            return False
    
    def run_tests(self):
        """Run all API tests."""
        # Start the server
        self.start_server()
        
        # Run tests
        root_success = self.test_root_endpoint()
        status_success = self.test_status_endpoint()
        question_success = self.test_question_endpoint()
        event_success = self.test_event_endpoint()
        
        # Print summary
        logger.info("\n=== API Test Summary ===")
        logger.info(f"Root Endpoint Test: {'PASSED' if root_success else 'FAILED'}")
        logger.info(f"Status Endpoint Test: {'PASSED' if status_success else 'FAILED'}")
        logger.info(f"Question Endpoint Test: {'PASSED' if question_success else 'FAILED'}")
        logger.info(f"Event Endpoint Test: {'PASSED' if event_success else 'FAILED'}")
        
        if root_success and status_success and question_success and event_success:
            logger.info("All API tests PASSED!")
            return 0
        else:
            logger.error("Some API tests FAILED!")
            return 1

def main():
    """Run the API tests."""
    tester = APITester()
    return tester.run_tests()

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
