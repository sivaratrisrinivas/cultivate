"""
Pytest configuration file for the Cultivate project.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create mock for aptos_sdk to avoid import errors
sys.modules['aptos_sdk'] = MagicMock()
sys.modules['aptos_sdk.async_client'] = MagicMock()
sys.modules['aptos_sdk.account'] = MagicMock()
sys.modules['aptos_sdk.transactions'] = MagicMock()

# Import project modules
from config import Config
from utils.logger import get_logger
from utils.cache import Cache

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock(spec=Config)
    
    # Set up blockchain config
    config.BLOCKCHAIN = {
        "NODE_URL": "https://fullnode.testnet.aptoslabs.com/v1",
        "NETWORK": "testnet",
        "EXPLORER_URL": "https://explorer.aptoslabs.com",
        "CACHE_TTL": 300
    }
    
    # Set up AI config
    config.AI = {
        "API_KEY": "test_api_key",
        "API_URL": "https://api.x.ai/v1",
        "MODEL": "grok-2-test",
        "TEMPERATURE": 0.7
    }
    
    # Set up notification config
    config.NOTIFICATIONS = {
        "ENABLED": True,
        "CHANNELS": ["console", "file"],
        "MIN_IMPORTANCE": 0.7
    }
    
    return config

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return get_logger("test")

@pytest.fixture
def mock_cache():
    """Create a mock cache for testing."""
    return Cache()

@pytest.fixture
def sample_blockchain_event_data():
    """Sample blockchain event data for testing."""
    return {
        "nft_mint": {
            "event_type": "nft_mint",
            "category": "nft",
            "data": {
                "blockchain": "Aptos",
                "collection_name": "Test Collection",
                "creator": "0x123",
                "name": "Test NFT #1",
                "amount": 1,
                "type": "NFT_MINT"
            },
            "importance_score": 0.85
        },
        "token_transfer": {
            "event_type": "token_event",
            "category": "transfer",
            "data": {
                "blockchain": "Aptos",
                "amount": 1000000,
                "token_name": "APT",
                "from": "0x456",
                "to": "0x789",
                "event_subtype": "large_transfer"
            },
            "importance_score": 0.9
        },
        "contract_deploy": {
            "event_type": "contract_event",
            "category": "contract",
            "data": {
                "blockchain": "Aptos",
                "address": "0xabc",
                "module_name": "test_module",
                "event_subtype": "contract_deployed"
            },
            "importance_score": 0.8
        }
    }
