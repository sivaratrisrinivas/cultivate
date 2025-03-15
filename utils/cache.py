# utils/cache.py
import json
import os
from datetime import datetime
import threading

class Cache:
    """Simple cache implementation with file persistence."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one cache instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Cache, cls).__new__(cls)
                cls._instance.initialize()
            return cls._instance
    
    def initialize(self):
        """Initialize the cache."""
        self.memory_cache = {}
        self.cache_dir = 'cache'
        
        # Create cache directory if needed
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def set(self, key, value, ttl=None):
        """Store a value in the cache."""
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': value,
            'ttl': ttl  # Time to live in seconds
        }
        
        # Store in memory
        self.memory_cache[key] = cache_data
        
        # Persist to disk
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            with open(file_path, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Error writing cache to disk: {str(e)}")
    
    def get(self, key, default=None):
        """Retrieve a value from the cache."""
        # Try memory cache first
        if key in self.memory_cache:
            cache_data = self.memory_cache[key]
            
            # Check ttl if set
            if cache_data.get('ttl'):
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                elapsed = (datetime.now() - cached_time).total_seconds()
                if elapsed > cache_data['ttl']:
                    return default
                    
            return cache_data['data']
        
        # Try disk cache
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    cache_data = json.load(f)
                
                # Check ttl if set
                if cache_data.get('ttl'):
                    cached_time = datetime.fromisoformat(cache_data['timestamp'])
                    elapsed = (datetime.now() - cached_time).total_seconds()
                    if elapsed > cache_data['ttl']:
                        return default
                
                # Update memory cache
                self.memory_cache[key] = cache_data
                
                return cache_data['data']
        except Exception as e:
            print(f"Error reading cache from disk: {str(e)}")
        
        return default
    
    def clear(self, key=None):
        """Clear specific key or entire cache."""
        if key:
            # Clear specific key
            if key in self.memory_cache:
                del self.memory_cache[key]
                
            # Remove from disk
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            # Clear all
            self.memory_cache = {}
            
            # Clear disk cache
            for file_name in os.listdir(self.cache_dir):
                if file_name.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file_name))
