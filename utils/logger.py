# utils/logger.py
import logging
import os
from datetime import datetime

def get_logger(name):
    """Set up a logger with the given name."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logger
    logger = logging.getLogger(name)
    
    # Skip if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # File handler with daily rotation
    log_file = f'logs/{name}-{datetime.now().strftime("%Y-%m-%d")}.log'
    file_handler = logging.FileHandler(log_file)
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
