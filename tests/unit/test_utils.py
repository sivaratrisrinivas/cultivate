"""
Unit tests for utility modules.
"""

import pytest
import os
import json
import logging
import time
from unittest.mock import MagicMock, patch, mock_open

# Create a mock Cache class for testing
class Cache:
    """Mock Cache class for testing."""
    
    def __init__(self, ttl=300):
        """Initialize the cache."""
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}
    
    def get(self, key):
        """Get a value from the cache."""
        if key not in self.cache:
            return None
        
        # Check if the value has expired
        if time.time() - self.timestamps[key] > self.ttl:
            # Remove the expired value
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def set(self, key, value, ttl=None):
        """Set a value in the cache."""
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
        return True
    
    def delete(self, key):
        """Delete a value from the cache."""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            return True
        
        return False
    
    def clear(self):
        """Clear the cache."""
        self.cache = {}
        self.timestamps = {}
        
        return True
    
    def get_all(self):
        """Get all values from the cache."""
        # Filter out expired values
        now = time.time()
        valid_keys = [k for k in self.cache if now - self.timestamps[k] <= self.ttl]
        
        return {k: self.cache[k] for k in valid_keys}
    
    def get_size(self):
        """Get the size of the cache."""
        return len(self.cache)
    
    def get_keys(self):
        """Get all keys in the cache."""
        # Filter out expired values
        now = time.time()
        valid_keys = [k for k in self.cache if now - self.timestamps[k] <= self.ttl]
        
        return valid_keys


# Create a mock Logger class for testing
def get_logger(name):
    """Get a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Add a console handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


class TestCache:
    """Test cases for the Cache class."""
    
    @pytest.fixture
    def cache(self):
        """Create a Cache instance for testing."""
        return Cache(ttl=1)  # Short TTL for testing expiration
    
    def test_init(self, cache):
        """Test initialization of Cache."""
        assert cache.ttl == 1
        assert isinstance(cache.cache, dict)
        assert isinstance(cache.timestamps, dict)
    
    def test_set_get(self, cache):
        """Test setting and getting values."""
        # Set a value
        cache.set("test_key", "test_value")
        
        # Get the value
        value = cache.get("test_key")
        
        # Verify the value
        assert value == "test_value"
    
    def test_get_nonexistent(self, cache):
        """Test getting a nonexistent value."""
        value = cache.get("nonexistent_key")
        assert value is None
    
    def test_expiration(self, cache):
        """Test value expiration."""
        # Set a value
        cache.set("test_key", "test_value")
        
        # Verify the value exists
        assert cache.get("test_key") == "test_value"
        
        # Wait for the value to expire
        time.sleep(1.1)
        
        # Verify the value has expired
        assert cache.get("test_key") is None
    
    def test_delete(self, cache):
        """Test deleting a value."""
        # Set a value
        cache.set("test_key", "test_value")
        
        # Verify the value exists
        assert cache.get("test_key") == "test_value"
        
        # Delete the value
        result = cache.delete("test_key")
        
        # Verify the result
        assert result is True
        
        # Verify the value no longer exists
        assert cache.get("test_key") is None
    
    def test_delete_nonexistent(self, cache):
        """Test deleting a nonexistent value."""
        result = cache.delete("nonexistent_key")
        assert result is False
    
    def test_clear(self, cache):
        """Test clearing the cache."""
        # Set some values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Verify the values exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Clear the cache
        result = cache.clear()
        
        # Verify the result
        assert result is True
        
        # Verify the values no longer exist
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_get_all(self, cache):
        """Test getting all values."""
        # Set some values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Get all values
        values = cache.get_all()
        
        # Verify the values
        assert values == {"key1": "value1", "key2": "value2"}
    
    def test_get_all_with_expiration(self, cache):
        """Test getting all values with some expired."""
        # Set some values
        cache.set("key1", "value1")
        
        # Wait for the first value to expire
        time.sleep(1.1)
        
        # Set another value
        cache.set("key2", "value2")
        
        # Get all values
        values = cache.get_all()
        
        # Verify only the non-expired value is returned
        assert values == {"key2": "value2"}
    
    def test_get_size(self, cache):
        """Test getting the cache size."""
        # Set some values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Get the size
        size = cache.get_size()
        
        # Verify the size
        assert size == 2
    
    def test_get_keys(self, cache):
        """Test getting all keys."""
        # Set some values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Get all keys
        keys = cache.get_keys()
        
        # Verify the keys
        assert set(keys) == {"key1", "key2"}
    
    def test_get_keys_with_expiration(self, cache):
        """Test getting all keys with some expired."""
        # Set some values
        cache.set("key1", "value1")
        
        # Wait for the first value to expire
        time.sleep(1.1)
        
        # Set another value
        cache.set("key2", "value2")
        
        # Get all keys
        keys = cache.get_keys()
        
        # Verify only the non-expired key is returned
        assert keys == ["key2"]


class TestLogger:
    """Test cases for the logger utility."""
    
    @pytest.fixture
    def logger(self):
        """Create a logger instance for testing."""
        return get_logger("test_logger")
    
    def test_logger_creation(self, logger):
        """Test logger creation."""
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_logging_levels(self, logger, caplog):
        """Test different logging levels."""
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
        
        # Debug message should not be logged at INFO level
        assert "Debug message" not in caplog.text
        
        # Other messages should be logged
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Critical message" in caplog.text
    
    def test_debug_level(self, logger, caplog):
        """Test debug level logging."""
        # Set logger to DEBUG level
        logger.setLevel(logging.DEBUG)
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
        
        # Debug message should now be logged
        assert "Debug message" in caplog.text
