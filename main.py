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
        
        # Flag to control application running state
        self.running = True
    
    def _init_modules(self):
        """Initialize all application modules in the correct logical sequence."""
        logger.info("Initializing modules")
        
        # Step 1: Initialize blockchain monitor first as it's the data source
        self.blockchain_monitor = BlockchainMonitor(self.config)
        logger.info("Blockchain monitor initialized")
        
        # Step 2: Initialize AI module which will process data from blockchain monitor
        self.ai_module = AIModule(self.config)
        logger.info("AI module initialized")
        
        # Step 3: Initialize Discord bot which will use AI module to generate messages
        self.discord_bot = DiscordBot(self.config, self.ai_module)
        # Connect the blockchain monitor to the Discord bot
        self.discord_bot.set_blockchain_monitor(self.blockchain_monitor)
        logger.info("Discord bot initialized")
        
        # Step 4: Initialize API which will provide data to the frontend
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
            if hasattr(self, 'db'):
                self.db.store_event(event, insights)
            
            # Check if this event should trigger a notification
            if hasattr(self, '_should_notify') and self._should_notify(event):
                self._send_notification(event, insights)
                
            return insights
        except Exception as e:
            logger.error(f"Error processing blockchain event: {str(e)}")
            return None
    
    def _blockchain_worker(self):
        """Worker function for blockchain monitoring."""
        logger.info("Starting blockchain polling worker")
        
        # Set up polling interval
        polling_interval = self.config.BLOCKCHAIN["POLLING_INTERVAL"]
        logger.info(f"Polling interval set to {polling_interval} seconds")
        
        # Track consecutive empty polls to implement adaptive polling
        consecutive_empty_polls = 0
        max_consecutive_empty = 5  # After this many empty polls, we'll increase the interval temporarily
        
        # Set blockchain monitor to running state
        self.blockchain_monitor.running = True
        
        while self.blockchain_monitor.running:
            try:
                logger.info("Polling for blockchain events")
                start_time = time.time()
                
                # Poll for events
                events = self.blockchain_monitor.poll_for_events(self.discord_bot)
                
                # Calculate time taken
                elapsed = time.time() - start_time
                logger.debug(f"Polling completed in {elapsed:.2f} seconds")
                
                if events:
                    # Reset consecutive empty polls counter
                    consecutive_empty_polls = 0
                    
                    # Process events
                    logger.info(f"Found {len(events)} significant events")
                    
                    # Events are already processed by the blockchain monitor
                    self.processing_event = False
                else:
                    # Increment consecutive empty polls counter
                    consecutive_empty_polls += 1
                    logger.info("No significant events detected")
                
                # Adaptive polling: if we've had several empty polls, increase the interval temporarily
                current_interval = polling_interval
                if consecutive_empty_polls > max_consecutive_empty:
                    # Increase interval by 50% but cap at 2x the base interval
                    current_interval = min(polling_interval * 2, polling_interval * 1.5)
                    logger.debug(f"Adaptive polling: increasing interval to {current_interval} seconds after {consecutive_empty_polls} empty polls")
                
                # Wait for the next polling interval
                logger.info(f"Waiting for {current_interval} seconds until next poll")
                
                # Use a loop with small sleeps to allow for clean shutdown
                for _ in range(int(current_interval)):
                    if not self.blockchain_monitor.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in blockchain worker: {str(e)}")
                # Wait a bit before retrying after an error
                time.sleep(5)
    
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
