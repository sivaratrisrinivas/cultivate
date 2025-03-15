# main.py
import threading
import asyncio
import os
import time
import signal
import sys
from datetime import datetime
from config import Config
from modules.blockchain import BlockchainMonitor
from modules.ai import AIModule
from modules.discord_bot import DiscordBot
from api.app import create_app
from api.routes import initialize_modules
from utils.logger import get_logger
from utils.cache import Cache

# Set up logging
logger = get_logger("main")

class AptosAI:
    """Main application class for the Aptos AI Social Media Manager."""
    
    def __init__(self):
        """Initialize the application."""
        logger.info("Initializing Aptos AI Social Media Manager")
        
        # Create necessary directories
        for dir_path in ['data', 'cache', 'logs', 'templates/memes']:
            os.makedirs(dir_path, exist_ok=True)
        
        # Load configuration
        self.config = Config()
        
        # Validate configuration
        missing_vars = Config.validate()
        if missing_vars:
            logger.warning(f"Missing critical environment variables: {', '.join(missing_vars)}")
            logger.warning("Application may not function correctly")
        
        # Initialize modules
        self._init_modules()
        
        # Set up shutdown handler
        self._setup_shutdown_handler()
        
        # Flag to control sequential processing
        self.processing_event = False
    
    def _init_modules(self):
        """Initialize all application modules."""
        logger.info("Initializing modules")
        
        # Initialize blockchain monitor
        self.blockchain_monitor = BlockchainMonitor(self.config)
        logger.info("Blockchain monitor initialized")
        
        # Initialize AI module
        self.ai_module = AIModule(self.config)
        logger.info("AI module initialized")
        
        # Initialize Discord bot
        self.discord_bot = DiscordBot(self.config, self.ai_module)
        # Connect the blockchain monitor to the Discord bot
        self.discord_bot.set_blockchain_monitor(self.blockchain_monitor)
        logger.info("Discord bot initialized")
        
        # Initialize API
        self._initialize_api()
        logger.info("API initialized")
    
    def _initialize_api(self):
        """Initialize the API module."""
        try:
            # Import here to avoid circular imports
            from api.app import create_app
            from api.routes import initialize_modules
            
            # Create Flask app
            self.api_app = create_app(self.config)
            
            # Initialize API routes with module references
            initialize_modules(
                blockchain_monitor=self.blockchain_monitor,
                ai_module=self.ai_module,
                discord_bot=self.discord_bot
            )
            
            # Start API server in a separate thread
            self.api_thread = threading.Thread(
                target=self._api_worker,
                daemon=True
            )
            self.api_thread.start()
            
            logger.info("API module initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing API module: {str(e)}")
            return False
    
    def _setup_shutdown_handler(self):
        """Set up graceful shutdown handler."""
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            self._cleanup()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _cleanup(self):
        """Clean up resources before shutdown."""
        logger.info("Cleaning up before shutdown")
        # Any cleanup tasks can go here
    
    def process_blockchain_event(self, event):
        """Process a blockchain event and generate AI insights."""
        try:
            logger.info(f"Processing blockchain event: {event.get('description', 'Unknown event')}")
            
            # Extract relevant information from the event
            event_type = event.get("event_category", "other")
            event_data = event.get("data", {})
            
            # Generate AI insights based on the event
            insights = self.ai_module.generate_insights(event)
            
            # Store the event and insights in the database
            self.db.store_event(event, insights)
            
            # Check if this event should trigger a notification
            if self._should_notify(event):
                self._send_notification(event, insights)
                
            return insights
        except Exception as e:
            logger.error(f"Error processing blockchain event: {str(e)}")
            return None
    
    def _blockchain_worker(self):
        """Worker function to poll for blockchain events."""
        logger.info("Starting blockchain polling worker")
        
        try:
            # Register callback for blockchain events if not already registered
            if not self.blockchain_monitor.event_callbacks:
                self.blockchain_monitor.register_event_callback(self.process_blockchain_event)
            
            # Start polling for events
            while True:
                logger.info("Polling for blockchain events")
                
                # Poll for events and pass the Discord bot for direct notifications
                significant_events = self.blockchain_monitor.poll_for_events(discord_bot=self.discord_bot)
                
                if significant_events:
                    logger.info(f"Found {len(significant_events)} significant events")
                    # Events will be processed by the callback and sent to Discord
                else:
                    logger.info("No significant events detected")
                
                # Wait before next poll
                logger.info(f"Waiting for {self.config.BLOCKCHAIN['POLLING_INTERVAL']} seconds until next poll")
                time.sleep(self.config.BLOCKCHAIN["POLLING_INTERVAL"])
                
        except Exception as e:
            logger.error(f"Error in blockchain polling worker: {str(e)}")
    
    def _api_worker(self):
        """Worker function to run the API server."""
        logger.info("Starting API server thread")
        self.api_app.run(
            host=self.config.API["HOST"],
            port=self.config.API["PORT"]
        )
    
    def _discord_worker(self):
        """Worker function to run the Discord bot."""
        logger.info("Starting Discord bot thread")
        self.discord_bot.run()
    
    def run(self):
        """Run the application."""
        logger.info("Starting application")
        
        # Start blockchain monitoring in a separate thread
        self.blockchain_thread = threading.Thread(
            target=self._blockchain_worker,
            daemon=True
        )
        self.blockchain_thread.start()
        
        # Start Discord bot in a separate thread
        self.discord_thread = threading.Thread(
            target=self._discord_worker,
            daemon=True
        )
        self.discord_thread.start()
        
        # Run API server in the main thread
        logger.info("Starting API server on http://{}:{}".format(
            self.config.API["HOST"], 
            self.config.API["PORT"]
        ))
        # We don't need to run the API server here since it's already running in a separate thread
        # Just keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
    
if __name__ == "__main__":
    # Create and run application
    app = AptosAI()
    app.run()
