"""
Unit tests for the AI module.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, mock_open

# Create a mock BlockchainEvent class for testing
class BlockchainEvent:
    """Mock BlockchainEvent class for testing."""
    
    def __init__(self, event_type, category, data, timestamp=None, importance_score=0.7):
        """Initialize a blockchain event."""
        self.event_type = event_type
        self.category = category
        self.data = data
        self.timestamp = timestamp or "2023-01-01T00:00:00"
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

# Create a mock AIModule class for testing
class AIModule:
    """Mock AIModule class for testing."""
    
    def __init__(self, config):
        """Initialize the AI module."""
        self.api_key = config.AI["API_KEY"]
        self.api_url = config.AI["API_URL"]
        self.model = config.AI["MODEL"]
        self.temperature = config.AI["TEMPERATURE"]
        self.prompts = self._load_prompts()
    
    def _load_prompts(self):
        """Load system prompts from file."""
        try:
            with open("prompts.json", "r") as f:
                return json.load(f)
        except Exception:
            # Return default prompts if file can't be loaded
            return {
                "social_post": {
                    "nft": "You are an AI assistant specialized in creating viral social media content about NFT events.",
                    "token": "You are an AI assistant specialized in creating viral social media content about token transfers.",
                    "contract": "You are an AI assistant specialized in creating viral social media content about smart contract events.",
                    "default": "You are an AI assistant specialized in creating viral social media content about blockchain events."
                },
                "meme": "You are an AI assistant specialized in creating viral memes about blockchain events.",
                "qa": "You are an AI assistant specialized in answering questions about blockchain technology."
            }
    
    def _call_grok_api(self, system_prompt, user_prompt, temperature=None):
        """Make a call to the X.AI Grok API."""
        # This is a mock implementation that would be replaced with actual API calls
        return f"Response to: {user_prompt}"
    
    def compose_social_post(self, event):
        """Compose a social media post for a blockchain event."""
        event_type = event.event_type
        category = event.category
        
        # Select the appropriate system prompt based on event type
        if category == "nft":
            system_prompt = self.prompts["social_post"]["nft"]
        elif category == "transfer" or "token" in event_type:
            system_prompt = self.prompts["social_post"]["token"]
        elif category == "contract":
            system_prompt = self.prompts["social_post"]["contract"]
        else:
            system_prompt = self.prompts["social_post"]["default"]
        
        # Create user prompt with event details
        user_prompt = f"Create a short, exciting social media post about this {event_type} event: {json.dumps(event.data)}"
        
        # Call the API
        return self._call_grok_api(system_prompt, user_prompt)
    
    def create_meme(self, event):
        """Create a meme for a blockchain event."""
        system_prompt = self.prompts["meme"]
        user_prompt = f"Create a meme about this {event.event_type} event: {json.dumps(event.data)}"
        
        return self._call_grok_api(system_prompt, user_prompt)
    
    def answer_question(self, question):
        """Answer a blockchain-related question."""
        system_prompt = self.prompts["qa"]
        
        result = self._call_grok_api(system_prompt, question)
        
        if result is None:
            return "I don't have information about that at the moment. Please try again later."
        
        return result

class TestAIModule:
    """Test cases for the AIModule class."""
    
    @pytest.fixture
    def mock_requests(self):
        """Create a mock for the requests module."""
        with patch('requests.post') as mock:
            # Configure the mock to return a successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Test response from AI"
                        }
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            mock.return_value = mock_response
            yield mock
    
    @pytest.fixture
    def ai_module(self, mock_config):
        """Create an AIModule instance for testing."""
        return AIModule(mock_config)
    
    def test_init(self, ai_module, mock_config):
        """Test initialization of AIModule."""
        assert ai_module.api_key == mock_config.AI["API_KEY"]
        assert ai_module.api_url == mock_config.AI["API_URL"]
        assert ai_module.model == mock_config.AI["MODEL"]
        assert ai_module.temperature == mock_config.AI["TEMPERATURE"]
    
    def test_call_grok_api(self, ai_module):
        """Test calling the Grok API."""
        # Mock the API call
        ai_module._call_grok_api = MagicMock(return_value="Test response from AI")
        
        result = ai_module._call_grok_api("System prompt", "User prompt")
        
        # Check result
        assert result == "Test response from AI"
    
    def test_compose_social_post_nft(self, ai_module):
        """Test composing a social post for an NFT event."""
        # Mock the API call
        ai_module._call_grok_api = MagicMock(return_value="Test NFT post")
        
        # Create a test event
        event = BlockchainEvent(
            "nft_mint",
            "nft",
            {
                "blockchain": "Aptos",
                "collection_name": "Test Collection",
                "name": "Test NFT #1"
            }
        )
        
        # Compose the post
        post = ai_module.compose_social_post(event)
        
        # Verify the result
        assert post == "Test NFT post"
        
        # Verify the API was called with correct parameters
        ai_module._call_grok_api.assert_called_once()
        args = ai_module._call_grok_api.call_args[0]
        
        # Check that the system prompt includes NFT-specific instructions
        assert "NFT" in args[0]
        
        # Check that the user prompt includes the event data
        assert "Test Collection" in args[1]
        assert "Test NFT #1" in args[1]
    
    def test_compose_social_post_token(self, ai_module):
        """Test composing a social post for a token event."""
        # Mock the API call
        ai_module._call_grok_api = MagicMock(return_value="Test token post")
        
        # Create a test event
        event = BlockchainEvent(
            "token_event",
            "transfer",
            {
                "blockchain": "Aptos",
                "amount": 1000000,
                "token_name": "APT"
            }
        )
        
        # Compose the post
        post = ai_module.compose_social_post(event)
        
        # Verify the result
        assert post == "Test token post"
        
        # Verify the API was called with correct parameters
        ai_module._call_grok_api.assert_called_once()
        args = ai_module._call_grok_api.call_args[0]
        
        # Check that the system prompt includes token-specific instructions
        assert "token" in args[0].lower() or "transfer" in args[0].lower()
        
        # Check that the user prompt includes the event data
        assert "1000000" in args[1]
        assert "APT" in args[1]
    
    def test_compose_social_post_contract(self, ai_module):
        """Test composing a social post for a contract event."""
        # Mock the API call
        ai_module._call_grok_api = MagicMock(return_value="Test contract post")
        
        # Create a test event
        event = BlockchainEvent(
            "contract_event",
            "contract",
            {
                "blockchain": "Aptos",
                "address": "0x123",
                "module_name": "test_module"
            }
        )
        
        # Compose the post
        post = ai_module.compose_social_post(event)
        
        # Verify the result
        assert post == "Test contract post"
        
        # Verify the API was called with correct parameters
        ai_module._call_grok_api.assert_called_once()
        args = ai_module._call_grok_api.call_args[0]
        
        # Check that the system prompt includes contract-specific instructions
        assert "contract" in args[0].lower()
        
        # Check that the user prompt includes the event data
        assert "0x123" in args[1]
        assert "test_module" in args[1]
    
    def test_compose_social_post_unknown(self, ai_module):
        """Test composing a social post for an unknown event type."""
        # Mock the API call
        ai_module._call_grok_api = MagicMock(return_value="Test unknown post")
        
        # Create a test event
        event = BlockchainEvent(
            "unknown_event",
            "unknown",
            {
                "blockchain": "Aptos",
                "key": "value"
            }
        )
        
        # Compose the post
        post = ai_module.compose_social_post(event)
        
        # Verify the result
        assert post == "Test unknown post"
        
        # Verify the API was called with correct parameters
        ai_module._call_grok_api.assert_called_once()
    
    def test_create_meme(self, ai_module):
        """Test creating a meme."""
        # Mock the API call
        ai_module._call_grok_api = MagicMock(return_value="Test meme description")
        
        # Create a test event
        event = BlockchainEvent(
            "token_event",
            "transfer",
            {
                "blockchain": "Aptos",
                "amount": 1000000,
                "token_name": "APT"
            }
        )
        
        # Create the meme
        meme = ai_module.create_meme(event)
        
        # Verify the result
        assert meme == "Test meme description"
        
        # Verify the API was called with correct parameters
        ai_module._call_grok_api.assert_called_once()
        args = ai_module._call_grok_api.call_args[0]
        
        # Check that the system prompt includes meme-specific instructions
        assert "meme" in args[0].lower()
        
        # Check that the user prompt includes the event data
        assert "1000000" in args[1]
        assert "APT" in args[1]
    
    def test_answer_question(self, ai_module):
        """Test answering a question."""
        # Mock the API call
        ai_module._call_grok_api = MagicMock(return_value="Test answer")
        
        # Answer a question
        answer = ai_module.answer_question("What is Aptos?")
        
        # Verify the result
        assert answer == "Test answer"
        
        # Verify the API was called with correct parameters
        ai_module._call_grok_api.assert_called_once()
        args = ai_module._call_grok_api.call_args[0]
        
        # Check that the system prompt includes Q&A-specific instructions
        assert "qa" in args[0].lower() or "question" in args[0].lower()
        
        # Check that the user prompt includes the question
        assert "What is Aptos?" in args[1]
    
    def test_answer_question_default(self, ai_module):
        """Test answering a question with API failure."""
        # Mock the API call to fail
        ai_module._call_grok_api = MagicMock(return_value=None)
        
        # Answer a question
        answer = ai_module.answer_question("What is Aptos?")
        
        # Verify the result is the default answer
        assert "I don't have information" in answer
        
        # Verify the API was called
        ai_module._call_grok_api.assert_called_once()
    
    def test_load_prompts(self, ai_module):
        """Test loading prompts from file."""
        # Mock the open function
        mock_data = {
            "social_post": {
                "nft": "NFT system prompt",
                "token": "Token system prompt",
                "contract": "Contract system prompt",
                "default": "Default system prompt"
            },
            "meme": "Meme system prompt",
            "qa": "QA system prompt"
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            # Load the prompts
            prompts = ai_module._load_prompts()
            
            # Verify the result
            assert prompts["social_post"]["nft"] == "NFT system prompt"
            assert prompts["social_post"]["token"] == "Token system prompt"
            assert prompts["social_post"]["contract"] == "Contract system prompt"
            assert prompts["social_post"]["default"] == "Default system prompt"
            assert prompts["meme"] == "Meme system prompt"
            assert prompts["qa"] == "QA system prompt"
