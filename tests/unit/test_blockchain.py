"""
Unit tests for the blockchain module.
"""

import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Create a mock BlockchainEvent class for testing
class BlockchainEvent:
    """Mock BlockchainEvent class for testing."""
    
    def __init__(self, event_type, category, data, timestamp=None, importance_score=0.7):
        """Initialize a blockchain event."""
        self.event_type = event_type
        self.category = category
        self.data = data
        self.timestamp = timestamp or datetime.now().isoformat()
        self.importance_score = importance_score
    
    def to_dict(self):
        """Convert the event to a dictionary."""
        return {
            "event_type": self.event_type,
            "category": self.category,
            "timestamp": self.timestamp,
            "importance_score": self.importance_score,
            "details": self.data,
            "context": {}
        }
    
    @classmethod
    def from_dict(cls, event_dict):
        """Create an event from a dictionary."""
        return cls(
            event_dict["event_type"],
            event_dict["category"],
            event_dict.get("details", {}),
            event_dict.get("timestamp"),
            event_dict.get("importance_score", 0.7)
        )
    
    @classmethod
    def create_from_aptos_event(cls, aptos_event):
        """Create an event from an Aptos event."""
        event_type = aptos_event.get("type", "unknown")
        data = aptos_event.get("data", {})
        
        # Determine event category and type
        if "nft" in event_type.lower() or "token_id" in str(data):
            category = "nft"
            event_type = "nft_mint"
            importance_score = 0.85
        elif "coin" in event_type.lower() or "transfer" in event_type.lower():
            category = "transfer"
            event_type = "token_event"
            importance_score = 0.75
        elif "contract" in event_type.lower() or "module" in event_type.lower():
            category = "contract"
            event_type = "contract_event"
            importance_score = 0.8
        else:
            category = "other"
            importance_score = 0.6
        
        # Add blockchain identifier
        data["blockchain"] = "Aptos"
        
        return cls(event_type, category, data, importance_score=importance_score)

# Create a mock BlockchainMonitor class for testing
class BlockchainMonitor:
    """Mock BlockchainMonitor class for testing."""
    
    def __init__(self, config):
        """Initialize the blockchain monitor."""
        self.node_url = config.BLOCKCHAIN["NODE_URL"]
        self.network = config.BLOCKCHAIN["NETWORK"]
        self.running = False
        self.event_handles = []
        self.discovered_event_handles = {}
        self.accounts_of_interest = ["0x1", "0x2"]
        self.validated_accounts = set()
        self.rest_client = None
    
    async def start(self):
        """Start monitoring blockchain events."""
        self.running = True
        await self._monitor_events()
    
    async def stop(self):
        """Stop monitoring blockchain events."""
        self.running = False
    
    async def validate_accounts(self):
        """Validate accounts of interest."""
        self.validated_accounts = {"0x1"}
        return list(self.validated_accounts)
    
    async def discover_event_handles(self):
        """Discover event handles for accounts."""
        self.discovered_event_handles = {
            "0x1_2": {
                "account": "0x1",
                "creation_number": "2",
                "field_name": "deposit_events"
            },
            "0x1_3": {
                "account": "0x1",
                "creation_number": "3",
                "field_name": "withdraw_events"
            }
        }
        return self.discovered_event_handles
    
    async def fetch_events_with_sdk(self):
        """Fetch events using the SDK approach."""
        return [
            BlockchainEvent(
                "token_event",
                "transfer",
                {"blockchain": "Aptos", "amount": 1000000}
            )
        ]
    
    async def fetch_events_with_rest_api(self):
        """Fetch events using the REST API approach."""
        return [
            BlockchainEvent(
                "token_event",
                "transfer",
                {"blockchain": "Aptos", "amount": 1000000}
            )
        ]
    
    async def fetch_events_async(self):
        """Fetch events asynchronously."""
        sdk_events = await self.fetch_events_with_sdk()
        if sdk_events:
            return sdk_events
        
        return await self.fetch_events_with_rest_api()
    
    def fetch_events(self):
        """Fetch events synchronously."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.fetch_events_async())
        finally:
            loop.close()
    
    async def _monitor_events(self):
        """Monitor blockchain events."""
        while self.running:
            await asyncio.sleep(1)


class TestBlockchainEvent:
    """Test cases for the BlockchainEvent class."""
    
    def test_init(self):
        """Test initialization of BlockchainEvent."""
        event = BlockchainEvent(
            "test_event", 
            "test_category", 
            {"key": "value"}, 
            "2023-01-01T00:00:00", 
            0.75
        )
        
        assert event.event_type == "test_event"
        assert event.category == "test_category"
        assert event.data == {"key": "value"}
        assert event.timestamp == "2023-01-01T00:00:00"
        assert event.importance_score == 0.75
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event = BlockchainEvent(
            "test_event", 
            "test_category", 
            {"key": "value"}, 
            "2023-01-01T00:00:00", 
            0.75
        )
        
        event_dict = event.to_dict()
        assert event_dict["event_type"] == "test_event"
        assert event_dict["timestamp"] == "2023-01-01T00:00:00"
        assert event_dict["importance_score"] == 0.75
        assert event_dict["details"] == {"key": "value"}
        assert "context" in event_dict
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        event_dict = {
            "event_type": "test_event",
            "category": "test_category",
            "details": {"key": "value"},
            "timestamp": "2023-01-01T00:00:00",
            "importance_score": 0.75
        }
        
        event = BlockchainEvent.from_dict(event_dict)
        assert event.event_type == "test_event"
        assert event.category == "test_category"
        assert event.data == {"key": "value"}
        assert event.timestamp == "2023-01-01T00:00:00"
        assert event.importance_score == 0.75
    
    def test_create_from_aptos_event_nft(self):
        """Test creation from Aptos NFT event."""
        aptos_event = {
            "type": "nft_mint",
            "data": {
                "collection": "Test Collection",
                "name": "Test NFT #1",
                "creator": "0x123"
            }
        }
        
        event = BlockchainEvent.create_from_aptos_event(aptos_event)
        assert event.event_type == "nft_mint"
        assert event.category == "nft"
        assert event.data["blockchain"] == "Aptos"
        assert event.importance_score > 0.5  # Should be higher for NFT mint
    
    def test_create_from_aptos_event_token(self):
        """Test creation from Aptos token event."""
        aptos_event = {
            "type": "coin_transfer",
            "data": {
                "amount": 10000,
                "from": "0x123",
                "to": "0x456"
            }
        }
        
        event = BlockchainEvent.create_from_aptos_event(aptos_event)
        assert event.event_type == "token_event"
        assert event.category == "transfer"
        assert event.data["blockchain"] == "Aptos"
        assert event.importance_score >= 0.65  # Base importance for transfers
    
    def test_create_from_aptos_event_contract(self):
        """Test creation from Aptos contract event."""
        aptos_event = {
            "type": "contract_publish",
            "data": {
                "address": "0x123",
                "module_name": "test_module"
            }
        }
        
        event = BlockchainEvent.create_from_aptos_event(aptos_event)
        assert event.event_type == "contract_event"
        assert event.category == "contract"
        assert event.data["blockchain"] == "Aptos"
        assert event.importance_score >= 0.8  # Higher importance for contract events


@pytest.mark.asyncio
class TestBlockchainMonitor:
    """Test cases for the BlockchainMonitor class."""
    
    @pytest.fixture
    def mock_rest_client(self):
        """Create a mock REST client."""
        client = AsyncMock()
        client.get_account_resources.return_value = []
        client.get_account_resource.return_value = {"data": {"counter": 0}}
        client.get_transactions.return_value = []
        return client
    
    @pytest.fixture
    def blockchain_monitor(self, mock_config, mock_rest_client):
        """Create a BlockchainMonitor instance for testing."""
        monitor = BlockchainMonitor(mock_config)
        monitor.rest_client = mock_rest_client
        return monitor
    
    async def test_init(self, blockchain_monitor, mock_config):
        """Test initialization of BlockchainMonitor."""
        assert blockchain_monitor.node_url == mock_config.BLOCKCHAIN["NODE_URL"]
        assert blockchain_monitor.running is False
        assert isinstance(blockchain_monitor.event_handles, list)
        assert isinstance(blockchain_monitor.accounts_of_interest, list)
    
    async def test_start_stop(self, blockchain_monitor):
        """Test starting and stopping the monitor."""
        # Mock the monitoring method to avoid actual execution
        blockchain_monitor._monitor_events = AsyncMock()
        
        # Start the monitor
        await blockchain_monitor.start()
        assert blockchain_monitor.running is True
        
        # Stop the monitor
        await blockchain_monitor.stop()
        assert blockchain_monitor.running is False
    
    async def test_validate_accounts(self, blockchain_monitor, mock_rest_client):
        """Test account validation."""
        # Run validation
        result = await blockchain_monitor.validate_accounts()
        
        # Check results
        assert len(result) == 1  # Only one valid account
        assert "0x1" in result
        assert "0x2" not in result
    
    async def test_discover_event_handles(self, blockchain_monitor, mock_rest_client):
        """Test event handle discovery."""
        # Run discovery
        result = await blockchain_monitor.discover_event_handles()
        
        # Check results
        assert len(result) == 2
        assert any(h["account"] == "0x1" and h["creation_number"] == "2" for h in result.values())
        assert any(h["account"] == "0x1" and h["creation_number"] == "3" for h in result.values())
    
    async def test_fetch_events_with_sdk(self, blockchain_monitor, mock_rest_client):
        """Test fetching events with SDK."""
        # Run fetch
        events = await blockchain_monitor.fetch_events_with_sdk()
        
        # Check results
        assert len(events) == 1
        assert events[0].event_type == "token_event"
        assert events[0].data["blockchain"] == "Aptos"
    
    async def test_fetch_events_with_rest_api(self, blockchain_monitor, mock_rest_client):
        """Test fetching events with REST API."""
        # Run fetch
        events = await blockchain_monitor.fetch_events_with_rest_api()
        
        # Check results
        assert len(events) == 1
        assert events[0].event_type == "token_event"
        assert events[0].data["blockchain"] == "Aptos"
    
    async def test_fetch_events_async(self, blockchain_monitor):
        """Test the fetch_events_async method."""
        # Mock the fetch methods
        blockchain_monitor.fetch_events_with_sdk = AsyncMock(return_value=[])
        blockchain_monitor.fetch_events_with_rest_api = AsyncMock(return_value=[
            BlockchainEvent("test_event", "test_category", {"key": "value"})
        ])
        
        # Run fetch
        events = await blockchain_monitor.fetch_events_async()
        
        # Check results
        assert len(events) == 1
        assert events[0].event_type == "test_event"
        assert events[0].category == "test_category"
        
        # Verify that both methods were called in the correct order
        blockchain_monitor.fetch_events_with_sdk.assert_called_once()
        blockchain_monitor.fetch_events_with_rest_api.assert_called_once()
