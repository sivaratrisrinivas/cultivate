# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration settings."""
    
    # Blockchain configuration
    BLOCKCHAIN = {
        "NODE_URL": os.getenv('APTOS_NODE_URL', 'https://fullnode.mainnet.aptoslabs.com/v1'),
        "POLLING_INTERVAL": int(os.getenv('POLLING_INTERVAL', 60)),
        "NETWORK": os.getenv('APTOS_NETWORK', 'mainnet')
    }
    
    # Discord configuration
    DISCORD = {
        "BOT_TOKEN": os.getenv('DISCORD_BOT_TOKEN'),
        "CHANNEL_ID": int(os.getenv('DISCORD_CHANNEL_ID', 0)),
        "PREFIX": os.getenv('DISCORD_PREFIX', '!')
    }
    
    # Discord configuration for notifications
    DISCORD_NOTIFICATIONS = {
        "WEBHOOK_URL": os.getenv('DISCORD_WEBHOOK_URL', ''),
        "NOTIFICATION_THRESHOLD": float(os.getenv('DISCORD_NOTIFICATION_THRESHOLD', 0.8))
    }
    
    # X.AI Grok configuration
    AI = {
        "API_KEY": os.getenv('XAI_API_KEY'),
        "API_URL": os.getenv('XAI_API_URL', 'https://api.x.ai/v1'),
        "MODEL": os.getenv('GROK_MODEL', 'grok-2-latest'),
        "TEMPERATURE": float(os.getenv('AI_TEMPERATURE', 0.7))
    }
    
    # API configuration
    API = {
        "PORT": int(os.getenv('PORT', 5001)),
        "HOST": os.getenv('HOST', '0.0.0.0'),
        "DEBUG": os.getenv('API_DEBUG', 'false').lower() == 'true'
    }
    
    # Monitoring configuration
    MONITOR = {
        "ACCOUNTS": os.getenv('MONITOR_ACCOUNTS', '').split(',') if os.getenv('MONITOR_ACCOUNTS') else [],
        "TOKENS": os.getenv('MONITOR_TOKENS', '').split(',') if os.getenv('MONITOR_TOKENS') else [],
        "COLLECTIONS": os.getenv('MONITOR_COLLECTIONS', '').split(',') if os.getenv('MONITOR_COLLECTIONS') else []
    }

    @classmethod
    def validate(cls):
        """Validate essential configuration parameters."""
        missing = []
        
        if not cls.DISCORD["BOT_TOKEN"]:
            missing.append("DISCORD_BOT_TOKEN")
        
        if not cls.AI["API_KEY"]:
            missing.append("XAI_API_KEY")
            
        return missing
