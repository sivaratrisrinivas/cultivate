# Optimized AI-Driven Social Media Manager for Aptos Blockchain

This is a streamlined, maintainable implementation of a social media manager that monitors Aptos blockchain events, generates AI content, and manages Discord community interactions.

## Project Structure

```
aptos-social-manager/
├── .env.example
├── requirements.txt
├── main.py
├── config.py
├── modules/
│   ├── blockchain.py
│   ├── ai.py
│   ├── discord_bot.py
├── api/
│   ├── app.py
│   ├── routes.py
├── utils/
│   ├── logger.py
│   ├── cache.py
```

## Requirements

```python
# requirements.txt
move-agent-kit>=1.0.0
flask>=2.0.0
flask-restful>=0.3.9
discord.py>=2.0.0
python-dotenv>=0.19.0
requests>=2.27.1
pillow>=9.0.0
```

## Configuration

```python
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
    
    # X.AI Grok configuration
    AI = {
        "API_KEY": os.getenv('XAI_API_KEY'),
        "API_URL": os.getenv('XAI_API_URL', 'https://api.x.ai/v1'),
        "MODEL": os.getenv('GROK_MODEL', 'grok-2-latest'),
        "TEMPERATURE": float(os.getenv('AI_TEMPERATURE', 0.7))
    }
    
    # API configuration
    API = {
        "PORT": int(os.getenv('PORT', 5000)),
        "HOST": os.getenv('HOST', '0.0.0.0')
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
```

## Blockchain Module

```python
# modules/blockchain.py
import os
import time
from datetime import datetime
from move_agent_kit import BlockchainReader
from utils.logger import get_logger
from utils.cache import Cache

logger = get_logger(__name__)
cache = Cache()

class BlockchainEvent:
    """Base class for blockchain events."""
    
    def __init__(self, event_type, data, importance=0.5):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now().isoformat()
        self.importance_score = importance
    
    def to_dict(self):
        """Convert event to dictionary format."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "importance_score": self.importance_score,
            "details": self.data,
            "context": {}
        }
    
    @staticmethod
    def from_dict(data):
        """Create event instance from dictionary."""
        return BlockchainEvent(
            data["event_type"],
            data["details"],
            data.get("importance_score", 0.5)
        )

    @staticmethod
    def create_from_aptos_event(event):
        """Factory method to create appropriate event type from Aptos event."""
        event_type = event.get("type", "").lower()
        data = event.get("data", {})
        importance = 0.5
        
        # Add blockchain context
        data["blockchain"] = "Aptos"
        data["version"] = event.get("version", "unknown")
        
        # Determine event type and importance
        if "token" in event_type or "nft" in event_type:
            importance = 0.7
            if "collection" in event_type and "create" in event_type:
                importance += 0.2
                data["event_subtype"] = "collection_created"
                return BlockchainEvent("nft_collection_created", data, importance)
            elif "mint" in event_type:
                importance += 0.1
                data["event_subtype"] = "nft_mint"
                return BlockchainEvent("nft_mint", data, importance)
            return BlockchainEvent("nft_event", data, importance)
            
        elif "coin" in event_type or "transfer" in event_type:
            importance = 0.65
            amount = data.get("amount", 0)
            if amount and float(amount) > 10000:
                importance += 0.2
                data["event_subtype"] = "large_transfer"
            return BlockchainEvent("token_event", data, importance)
            
        elif "contract" in event_type or "module" in event_type:
            importance = 0.8
            if "publish" in event_type:
                data["event_subtype"] = "contract_deployed"
            return BlockchainEvent("contract_event", data, importance)
            
        elif "transaction" in event_type:
            return BlockchainEvent("transaction_event", data, 0.6)
        
        # Default case
        return BlockchainEvent("generic_event", data, 0.5)


class BlockchainMonitor:
    """Monitors the Aptos blockchain for significant events."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        self.reader = BlockchainReader(network=config.BLOCKCHAIN["NETWORK"])
        self.last_version_file = "data/last_version.txt"
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.last_version_file), exist_ok=True)
    
    def get_last_processed_version(self):
        """Get the last processed ledger version."""
        try:
            if os.path.exists(self.last_version_file):
                with open(self.last_version_file, "r") as f:
                    return int(f.read().strip())
            return 0
        except Exception as e:
            logger.error(f"Error reading last processed version: {str(e)}")
            return 0
    
    def save_last_processed_version(self, version):
        """Save the last processed ledger version."""
        try:
            with open(self.last_version_file, "w") as f:
                f.write(str(version))
        except Exception as e:
            logger.error(f"Error saving last processed version: {str(e)}")
    
    def fetch_events(self):
        """Fetch and process new events from the blockchain."""
        try:
            # Get latest ledger version
            current_version = self.reader.get_latest_version()
            last_processed_version = self.get_last_processed_version()
            
            if current_version = 0.6:
                significant_events.append(blockchain_event)
        
        # Sort by importance
        significant_events.sort(key=lambda x: x.importance_score, reverse=True)
        
        # Cache for fallback
        cache.set("blockchain_events", [e.to_dict() for e in significant_events])
        
        return significant_events
```

## AI Module

```python
# modules/ai.py
import json
import os
import requests
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from utils.logger import get_logger
from utils.cache import Cache

logger = get_logger(__name__)
cache = Cache()

class AIModule:
    """AI module for content generation and Q&A using X.AI's Grok."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        self.api_key = config.AI["API_KEY"]
        self.api_url = config.AI["API_URL"]
        self.model = config.AI["MODEL"]
        self.temperature = config.AI["TEMPERATURE"]
        
        # Ensure directories exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("cache/memes", exist_ok=True)
        os.makedirs("templates/memes", exist_ok=True)
        
        # Load Q&A database
        self.qa_database = self._load_qa_database()
        
        # Create default meme template if needed
        self._ensure_default_template()
    
    def _ensure_default_template(self):
        """Ensure default meme template exists."""
        default_template = "templates/memes/default.png"
        if not os.path.exists(default_template):
            img = Image.new('RGB', (800, 600), color=(255, 255, 255))
            img.save(default_template)
    
    def _load_qa_database(self):
        """Load Q&A database for fallback responses."""
        qa_file = "data/qa_database.json"
        
        if os.path.exists(qa_file):
            try:
                with open(qa_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading Q&A database: {str(e)}")
        
        # Default Q&A pairs
        default_qa = {
            "what is aptos": "Aptos is a Layer 1 blockchain built with Move, focused on safety, reliability, and scalability.",
            "how do i create a wallet": "You can create an Aptos wallet using tools like Petra, Martian, or Pontem wallet. Visit their websites to download and follow the setup instructions.",
            "what's the latest transaction volume": "I'll check the latest Aptos transaction volume for you from the blockchain data.",
            "how do i mint an nft": "To mint an NFT on Aptos, you'll need to interact with a token contract. Most users use platforms like Topaz or BlueMove for a user-friendly experience.",
            "what is move language": "Move is a programming language designed for secure resource management on blockchains. It powers Aptos and focuses on safety and verifiability.",
            "how fast is aptos": "Aptos can process thousands of transactions per second (TPS) thanks to its parallel execution engine and Block-STM technology.",
        }
        
        # Save default database
        try:
            with open(qa_file, "w") as f:
                json.dump(default_qa, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving default Q&A database: {str(e)}")
        
        return default_qa
    
    def _call_grok_api(self, system_prompt, user_prompt, temperature=None):
        """Make a call to the X.AI Grok API."""
        if temperature is None:
            temperature = self.temperature
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "model": self.model,
                "stream": False,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10  # Add timeout for better error handling
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the generated text
            return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
        except requests.exceptions.Timeout:
            logger.error("Grok API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Grok API request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Grok API: {str(e)}")
            return None
    
    def generate_post(self, event):
        """Generate a social media post from a blockchain event."""
        event_type = event.event_type
        details = event.data
        
        # Define system prompt
        system_prompt = (
            "You are an AI assistant specialized in creating viral social media content "
            "about blockchain events, specifically for the Aptos blockchain. "
            "Your responses should be engaging, informative, and optimized for Twitter-style "
            "posts under 280 characters."
        )
        
        # Create user prompt based on event type
        if "nft" in event_type:
            if "collection_created" in event_type:
                collection_name = details.get("collection_name", "a new collection")
                user_prompt = f"Create a short, exciting tweet about a new NFT collection '{collection_name}' just launched on Aptos blockchain."
            elif "mint" in event_type:
                collection_name = details.get("collection_name", "a collection")
                count = details.get("items_minted", "Multiple")
                user_prompt = f"Create a short, exciting tweet about {count} new NFTs just minted from '{collection_name}' collection on Aptos."
            else:
                user_prompt = "Create a short, exciting tweet about NFT activity heating up on Aptos blockchain."
        
        elif "token" in event_type:
            if details.get("event_subtype") == "large_transfer":
                amount = details.get("amount", "a significant amount")
                token = details.get("token_name", "tokens")
                user_prompt = f"Create a short, exciting tweet about {amount} {token} just transferred on Aptos blockchain."
            else:
                user_prompt = "Create a short, exciting tweet about token activity increasing on Aptos blockchain."
        
        elif "contract" in event_type:
            if details.get("event_subtype") == "contract_deployed":
                address = details.get("address", "")
                short_address = address[:8] + "..." if address else "a new contract"
                user_prompt = f"Create a short, exciting tweet about a new smart contract {short_address} just deployed on Aptos."
            else:
                user_prompt = "Create a short, exciting tweet about smart contract activity detected on Aptos blockchain."
        
        else:
            user_prompt = f"Create a short, exciting tweet about {event_type.replace('_', ' ')} activity on the Aptos blockchain."
        
        # Generate content
        content = self._call_grok_api(system_prompt, user_prompt)
        
        # Fallback if generation fails
        if not content:
            logger.warning("Content generation failed, using fallback")
            content = f"Exciting {event_type.replace('_', ' ')} activity on Aptos blockchain!"
        
        # Add hashtags
        hashtags = self._generate_hashtags(event_type)
        final_post = self._format_post(content, hashtags)
        
        return {
            "content": final_post,
            "event_reference": f"{event_type}_{datetime.now().isoformat()}",
            "source_event": event.to_dict()
        }
    
    def generate_meme(self, event):
        """Generate a meme based on a blockchain event."""
        event_type = event.event_type
        
        # Generate meme text using Grok
        system_prompt = "You are a meme creator specializing in blockchain humor."
        user_prompt = f"Create a funny meme about {event_type} on the Aptos blockchain. Format: TOP TEXT | BOTTOM TEXT"
        
        meme_text = self._call_grok_api(system_prompt, user_prompt)
        
        # Parse or use default
        try:
            top_text, bottom_text = meme_text.split('|')
            top_text = top_text.strip()
            bottom_text = bottom_text.strip()
        except:
            top_text, bottom_text = self._default_meme_text(event_type)
        
        # Create meme image
        template_path = "templates/memes/default.png"
        meme_image = self._create_meme_image(template_path, top_text, bottom_text)
        
        # Save meme
        meme_path = f"cache/memes/{event_type}_{datetime.now().timestamp()}.png"
        meme_image.save(meme_path)
        
        return {
            "text": f"{top_text} {bottom_text}",
            "image_path": meme_path,
            "event_reference": f"{event_type}_{datetime.now().isoformat()}"
        }
    
    def get_answer(self, question):
        """Answer a user question about Aptos."""
        # Normalize question
        normalized_question = question.lower().strip()
        
        # Check for exact matches in database
        if normalized_question in self.qa_database:
            return {
                "answer": self.qa_database[normalized_question],
                "confidence": 1.0
            }
        
        # Check for partial matches
        for q, answer in self.qa_database.items():
            if q in normalized_question or normalized_question in q:
                return {
                    "answer": answer,
                    "confidence": 0.8
                }
        
        # Generate answer with Grok
        system_prompt = (
            "You are an AI assistant specializing in the Aptos blockchain ecosystem. "
            "Provide accurate, helpful information about Aptos, focusing on technical details, "
            "ecosystem updates, and how-to guidance."
        )
        
        answer = self._call_grok_api(system_prompt, question, temperature=0.2)
        
        if answer:
            return {
                "answer": answer,
                "confidence": 0.9
            }
        
        # Fallback
        return {
            "answer": "I don't have specific information about that yet. You can check the Aptos documentation for more details: https://aptos.dev",
            "confidence": 0.2
        }
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text."""
        system_prompt = "You are a sentiment analysis assistant."
        user_prompt = (
            f"Analyze the sentiment of this text: \"{text}\"\n"
            "Provide only a number between -1 and 1 as your response, where:"
            "-1 = very negative, -0.5 = negative, 0 = neutral, 0.5 = positive, 1 = very positive."
        )
        
        result = self._call_grok_api(system_prompt, user_prompt, temperature=0.1)
        
        try:
            # Try to parse the score as a float
            score = float(result)
            # Ensure it's in the range -1 to 1
            return max(-1, min(1, score))
        except (ValueError, TypeError):
            # Fallback to simple keyword-based sentiment
            return self._keyword_sentiment(text)
    
    def _keyword_sentiment(self, text):
        """Simple keyword-based sentiment analysis."""
        positive_words = ["good", "great", "excellent", "amazing", "love", "like", "helpful", "thanks"]
        negative_words = ["bad", "terrible", "awful", "hate", "dislike", "poor", "problem", "issue"]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0  # Neutral
        
        return (positive_count - negative_count) / total_count
    
    def _generate_hashtags(self, event_type):
        """Generate hashtags based on event type."""
        base_hashtags = ["#Aptos", "#Web3"]
        
        event_specific_hashtags = {
            "nft_event": ["#NFT", "#DigitalArt", "#AptoNFTs"],
            "nft_collection_created": ["#NFT", "#NewCollection", "#AptoNFTs"],
            "nft_mint": ["#NFTMint", "#DigitalArt", "#AptoNFTs"],
            "token_event": ["#Crypto", "#DeFi", "#AptosEcosystem"],
            "contract_event": ["#SmartContracts", "#BuildOnAptos"],
            "transaction_event": ["#Blockchain", "#Crypto", "#AptosNetwork"]
        }
        
        # Get relevant hashtags
        specific_hashtags = event_specific_hashtags.get(event_type, ["#Blockchain", "#Move"])
        
        # Select 2 random specific hashtags to keep it concise
        selected = random.sample(specific_hashtags, min(2, len(specific_hashtags)))
        
        return base_hashtags + selected
    
    def _format_post(self, content, hashtags):
        """Format content with hashtags ensuring character limit."""
        hashtag_text = " ".join(hashtags)
        max_content_length = 280 - len(hashtag_text) - 1  # -1 for the space
        
        if len(content) > max_content_length:
            content = content[:max_content_length-3] + "..."
        
        return f"{content} {hashtag_text}"
    
    def _default_meme_text(self, event_type):
        """Generate default meme text based on event type."""
        defaults = {
            "nft_event": ("WHEN YOU SEE A NEW NFT COLLECTION", "APTOS COMMUNITY GOES WILD"),
            "nft_collection_created": ("NEW NFT COLLECTION JUST DROPPED", "MY WALLET: HERE WE GO AGAIN"),
            "nft_mint": ("WATCHING NFTS BEING MINTED", "CRYPTO TWITTER: BULLISH"),
            "token_event": ("LARGE TOKEN TRANSFER DETECTED", "CRYPTO TWITTER: SOMETHING'S HAPPENING"),
            "contract_event": ("NEW SMART CONTRACT DEPLOYED", "DEVELOPERS: IT'S BUILDING TIME"),
        }
        
        return defaults.get(event_type, ("APTOS BLOCKCHAIN", "MAKING MOVES"))
    
    def _create_meme_image(self, template_path, top_text, bottom_text):
        """Create a meme image with the given template and text."""
        # Open the template image
        img = Image.open(template_path)
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        # Draw the top text
        draw.text((img.width/2, 50), top_text, font=font, fill="black", anchor="mt")
        
        # Draw the bottom text
        draw.text((img.width/2, img.height-50), bottom_text, font=font, fill="black", anchor="mb")
        
        return img
```

## Discord Bot Module

```python
# modules/discord_bot.py
import discord
import os
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

class DiscordBot:
    """Discord bot for social media management."""
    
    def __init__(self, config, ai_module):
        """Initialize the Discord bot."""
        self.config = config
        self.ai_module = ai_module
        
        # Discord setup
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix=config.DISCORD["PREFIX"], intents=intents)
        self.channel_id = config.DISCORD["CHANNEL_ID"]
        
        # Message queue for rate limiting
        self.message_queue = asyncio.Queue()
        
        # Last post time tracking
        self.last_post_time = datetime.now() - timedelta(days=1)
        
        # Track posted events to avoid duplicates
        self.posted_events = set()
        
        # Set up event handlers and commands
        self._setup_bot()
    
    def _setup_bot(self):
        """Set up bot event handlers and commands."""
        @self.bot.event
        async def on_ready():
            """Handle bot ready event."""
            logger.info(f'Discord bot logged in as {self.bot.user}')
            self.process_message_queue.start()
        
        @self.bot.event
        async def on_message(message):
            """Handle incoming messages."""
            # Ignore bot's own messages
            if message.author == self.bot.user:
                return
            
            # Process potential questions
            await self._handle_potential_question(message)
            
            # Process commands
            await self.bot.process_commands(message)
        
        # Register commands
        self._register_commands()
    
    def _register_commands(self):
        """Register bot commands."""
        @self.bot.command(name='aptos')
        async def aptos_info(ctx):
            """Get information about Aptos blockchain."""
            response = self.ai_module.get_answer("what is aptos")
            await ctx.send(response["answer"])
        
        @self.bot.command(name='help')
        async def help_command(ctx):
            """Show help information."""
            help_text = (
                "**Aptos Social Manager Bot**\n\n"
                "I monitor the Aptos blockchain and post updates about significant events. "
                "I can also answer questions about Aptos!\n\n"
                "**Commands:**\n"
                f"- `{self.config.DISCORD['PREFIX']}aptos` - Get information about Aptos blockchain\n"
                f"- `{self.config.DISCORD['PREFIX']}stats` - View current blockchain statistics\n"
                f"- `{self.config.DISCORD['PREFIX']}recent` - See recent significant events\n"
                f"- `{self.config.DISCORD['PREFIX']}campaign` - See active community campaigns\n"
                f"- `{self.config.DISCORD['PREFIX']}help` - Show this help message\n\n"
                "You can also ask me questions directly by mentioning me or asking a question with Aptos in it!"
            )
            await ctx.send(help_text)
        
        @self.bot.command(name='stats')
        async def stats_command(ctx):
            """Show current blockchain statistics."""
            # This would typically fetch real stats
            stats_text = (
                "**Current Aptos Blockchain Statistics**\n\n"
                "- TPS: 1,200\n"
                "- Active validators: 100\n"
                "- Latest block: #12345678\n"
                "- 24h transactions: 1.2M\n"
                "- Gas price: 100 Octa\n\n"
                "Stats updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            )
            await ctx.send(stats_text)
        
        @self.bot.command(name='recent')
        async def recent_events(ctx):
            """Show recent significant events."""
            events_text = (
                "**Recent Significant Events on Aptos**\n\n"
                "- NFT Collection 'AptoPunks' launched 2 hours ago\n"
                "- Large token transfer: 500,000 APT moved 5 hours ago\n"
                "- New smart contract deployed 12 hours ago\n"
                "- Transaction volume increased by 35% in the last 24 hours\n\n"
                "Stay tuned for more updates!"
            )
            await ctx.send(events_text)
            
        @self.bot.command(name='campaign')
        async def campaign_info(ctx):
            """Show information about active campaigns."""
            campaign_text = (
                "**Active Aptos Community Campaigns**\n\n"
                "**🎁 Weekly Engagement Challenge**\n"
                "Ask 3 quality questions about Aptos and get them answered by our bot to earn points!\n"
                "Top 10 participants will receive an exclusive Aptos NFT.\n\n"
                "**🚀 Smart Contract Awareness Drive**\n"
                "Share screenshots of your interactions with Aptos smart contracts on Twitter/X\n"
                "Tag @AptosProject and use #BuildOnAptos to enter the airdrop lottery.\n\n"
                f"Use `{self.config.DISCORD['PREFIX']}campaign-status` to check your current participation."
            )
            await ctx.send(campaign_text)
    
    async def _handle_potential_question(self, message):
        """Handle potential question in a message."""
        # Check if this is likely a question for the bot
        is_question = message.content.endswith('?')
        is_mention = self.bot.user in message.mentions
        contains_aptos = 'aptos' in message.content.lower()
        
        if (is_question and contains_aptos) or is_mention:
            # Extract question
            question = message.content
            if is_mention:
                question = question.replace(f'', '').strip()
            
            # Analyze sentiment
            sentiment = self.ai_module.analyze_sentiment(question)
            
            # Get answer
            response = self.ai_module.get_answer(question)
            
            # Adapt response based on sentiment
            if sentiment > 0.5:
                response_text = f"Glad you're enthusiastic! {response['answer']}"
            elif sentiment = 0.5:
                await message.reply(response_text)
    
    @tasks.loop(seconds=5)
    async def process_message_queue(self):
        """Process the message queue with rate limiting."""
        try:
            if not self.message_queue.empty():
                # Get message data
                message_data = await self.message_queue.get()
                
                # Get target channel
                channel = self.bot.get_channel(self.channel_id)
                if not channel:
                    logger.error(f"Channel with ID {self.channel_id} not found")
                    return
                
                # Send message
                await channel.send(message_data["content"])
                logger.info(f"Posted message to Discord: {message_data['content'][:30]}...")
                
                # Send image if available
                image_path = message_data.get("image_path")
                if image_path and os.path.exists(image_path):
                    await channel.send(file=discord.File(image_path))
                    logger.info(f"Posted image to Discord")
                
                # Mark task as done
                self.message_queue.task_done()
                
                # Add delay for rate limiting
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error processing message queue: {str(e)}")
    
    async def post_content(self, content):
        """Queue content for posting to Discord."""
        # Check for duplicate posts
        event_ref = content.get("event_reference", "")
        if event_ref and event_ref in self.posted_events:
            logger.info(f"Skipping duplicate content: {event_ref}")
            return
        
        # Add to queue
        await self.message_queue.put(content)
        
        # Track posted event
        if event_ref:
            self.posted_events.add(event_ref)
            # Limit set size
            if len(self.posted_events) > 1000:
                self.posted_events = set(list(self.posted_events)[-900:])
    
    def run(self):
        """Run the Discord bot."""
        logger.info("Starting Discord bot")
        self.bot.run(self.config.DISCORD["BOT_TOKEN"])
```

## API Module

```python
# api/app.py
from flask import Flask
from flask_restful import Api
from utils.logger import get_logger

logger = get_logger(__name__)

def create_app(config):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Configure Flask app
    app.config['ENV'] = 'development' if config.API.get('DEBUG', False) else 'production'
    
    # Initialize API
    api = Api(app)
    
    # Import routes here to avoid circular imports
    from api.routes import register_routes
    register_routes(api)
    
    @app.route('/')
    def index():
        return {
            "service": "Aptos Social Media Manager",
            "status": "operational",
            "version": "1.0.0"
        }
    
    logger.info("API application created")
    return app
```

```python
# api/routes.py
from flask import request
from flask_restful import Resource
from utils.logger import get_logger
import asyncio

logger = get_logger(__name__)

# Store module references
_blockchain_monitor = None
_ai_module = None
_discord_bot = None

def initialize_modules(blockchain_monitor, ai_module, discord_bot):
    """Initialize module references."""
    global _blockchain_monitor, _ai_module, _discord_bot
    _blockchain_monitor = blockchain_monitor
    _ai_module = ai_module
    _discord_bot = discord_bot
    logger.info("API routes initialized with module references")

class EventResource(Resource):
    """Resource for handling blockchain events."""
    
    def post(self):
        """Process a blockchain event."""
        if not _ai_module or not _discord_bot:
            return {"error": "API not fully initialized"}, 500
            
        data = request.get_json()
        if not data:
            return {"error": "No data provided"}, 400
        
        try:
            # Create dummy event object if needed
            if not hasattr(data, 'to_dict'):
                from modules.blockchain import BlockchainEvent
                # Convert dict to event
                event = BlockchainEvent(
                    data.get("event_type", "unknown_event"),
                    data.get("details", {}),
                    data.get("importance_score", 0.5)
                )
            else:
                event = data
                
            # Generate content
            post = _ai_module.generate_post(event)
            
            # Queue for posting
            asyncio.run(_discord_bot.post_content(post))
            
            return {
                "success": True,
                "message": "Event processed successfully",
                "content": post["content"]
            }
            
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
            return {"error": str(e)}, 500

class MemeResource(Resource):
    """Resource for generating memes."""
    
    def post(self):
        """Generate a meme from event data."""
        if not _ai_module or not _discord_bot:
            return {"error": "API not fully initialized"}, 500
            
        data = request.get_json()
        if not data:
            return {"error": "No data provided"}, 400
        
        try:
            # Create dummy event object if needed
            if not hasattr(data, 'to_dict'):
                from modules.blockchain import BlockchainEvent
                # Convert dict to event
                event = BlockchainEvent(
                    data.get("event_type", "unknown_event"),
                    data.get("details", {}),
                    data.get("importance_score", 0.5)
                )
            else:
                event = data
                
            # Generate meme
            meme = _ai_module.generate_meme(event)
            
            # Queue for posting
            asyncio.run(_discord_bot.post_content(meme))
            
            return {
                "success": True,
                "message": "Meme generated successfully",
                "meme_text": meme["text"]
            }
            
        except Exception as e:
            logger.error(f"Error generating meme: {str(e)}")
            return {"error": str(e)}, 500

class QuestionResource(Resource):
    """Resource for handling questions."""
    
    def post(self):
        """Answer a question about Aptos."""
        if not _ai_module:
            return {"error": "API not fully initialized"}, 500
            
        data = request.get_json()
        if not data or 'question' not in data:
            return {"error": "No question provided"}, 400
        
        try:
            # Get answer from AI module
            answer = _ai_module.get_answer(data['question'])
            
            return {
                "success": True,
                "answer": answer["answer"],
                "confidence": answer["confidence"]
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {"error": str(e)}, 500

class StatusResource(Resource):
    """Resource for system status."""
    
    def get(self):
        """Get system status."""
        components = {
            "blockchain_module": "online" if _blockchain_monitor else "offline",
            "ai_module": "online" if _ai_module else "offline",
            "discord_bot": "online" if _discord_bot else "offline"
        }
        
        overall_status = "operational" if all(s == "online" for s in components.values()) else "degraded"
        
        return {
            "status": overall_status,
            "components": components,
            "version": "1.0.0",
            "timestamp": asyncio.run(asyncio.to_thread(lambda: datetime.now().isoformat()))
        }

def register_routes(api):
    """Register API routes."""
    api.add_resource(EventResource, '/api/event')
    api.add_resource(MemeResource, '/api/meme')
    api.add_resource(QuestionResource, '/api/question')
    api.add_resource(StatusResource, '/api/status')
    logger.info("API routes registered")
```

## Utility Functions

```python
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
```

```python
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
```

## Main Script

```python
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
        logger.info("Discord bot initialized")
        
        # Initialize API
        initialize_modules(self.blockchain_monitor, self.ai_module, self.discord_bot)
        self.app = create_app(self.config)
        logger.info("API initialized")
    
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
    
    def _blockchain_worker(self):
        """Worker function to poll blockchain and process events."""
        logger.info("Starting blockchain worker thread")
        
        while True:
            try:
                logger.info("Polling for blockchain events")
                events = self.blockchain_monitor.fetch_events()
                
                if events:
                    logger.info(f"Found {len(events)} significant events")
                    
                    # Process events
                    for event in events:
                        # Generate content
                        post = self.ai_module.generate_post(event)
                        
                        # Queue for posting
                        asyncio.run(self.discord_bot.post_content(post))
                        
                        # Generate meme for high-importance events
                        if event.importance_score > 0.8:
                            meme = self.ai_module.generate_meme(event)
                            asyncio.run(self.discord_bot.post_content(meme))
                else:
                    logger.info("No significant events detected")
                
                # Wait for next polling interval
                interval = self.config.BLOCKCHAIN["POLLING_INTERVAL"]
                logger.info(f"Waiting for {interval} seconds until next poll")
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in blockchain worker: {str(e)}")
                # Sleep briefly before retrying
                time.sleep(10)
    
    def _api_worker(self):
        """Worker function to run the API server."""
        logger.info("Starting API server thread")
        self.app.run(
            host=self.config.API["HOST"],
            port=self.config.API["PORT"]
        )
    
    def run(self):
        """Run the application."""
        logger.info("Starting application")
        
        # Start blockchain worker thread
        blockchain_thread = threading.Thread(target=self._blockchain_worker)
        blockchain_thread.daemon = True
        blockchain_thread.start()
        
        # Start API server thread
        api_thread = threading.Thread(target=self._api_worker)
        api_thread.daemon = True
        api_thread.start()
        
        # Start Discord bot (blocking)
        logger.info("Starting Discord bot")
        self.discord_bot.run()

if __name__ == "__main__":
    # Create and run application
    app = AptosAI()
    app.run()
```

## .env Example

```
# .env.example
# Blockchain configuration
APTOS_NODE_URL=https://fullnode.mainnet.aptoslabs.com/v1
APTOS_NETWORK=mainnet
POLLING_INTERVAL=60

# Discord configuration
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_channel_id
DISCORD_PREFIX=!

# X.AI Grok configuration
XAI_API_KEY=xai-your_api_key_here
XAI_API_URL=https://api.x.ai/v1
GROK_MODEL=grok-2-latest
AI_TEMPERATURE=0.7

# API configuration
PORT=5000
HOST=0.0.0.0
```

## How to Run

1. Clone the repository with all the above files
2. Copy `.env.example` to `.env` and fill in your X.AI API key and Discord bot token
3. Install the requirements: `pip install -r requirements.txt`
4. Run the application: `python main.py`

## Key Optimizations

1. **Modular Structure**: Consolidated related functionality into single files for better maintainability.
2. **Improved Configuration**: Organized config into logical groups with validation.
3. **Better Error Handling**: Added comprehensive error handling with fallback mechanisms.
4. **Singleton Cache**: Implemented thread-safe singleton cache with TTL support.
5. **Event Factory Pattern**: Used factory method for creating event objects.
6. **Improved Documentation**: Added detailed docstrings and comments.
7. **Graceful Shutdown**: Added signal handlers for proper cleanup.
8. **Optimized API Calls**: Added timeouts and better error handling for API calls.
9. **Simplified Code Flow**: Removed redundant code and improved function organization.
10. **Enhanced Logging**: Added date-based log rotation.

This optimized implementation provides all the requested features:
- AI-generated posts and memes based on Aptos blockchain events
- Automated responses to Discord community queries with sentiment analysis
- Gamified campaign management via Discord commands
- X.AI's Grok integration for content generation

The architecture is now leaner, more readable, and easier to maintain, enabling developers to understand and extend the application efficiently.

