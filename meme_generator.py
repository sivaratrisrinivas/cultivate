"""
Meme generator module using X.AI's image generation API.
This can be integrated into the existing AI module.
"""

import json
import os
import requests
import random
import logging
from datetime import datetime
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemeGenerator:
    """Meme generator using X.AI's image generation API."""
    
    def __init__(self, config):
        """Initialize with configuration.
        
        Args:
            config: Configuration object with AI settings
        """
        self.config = config
        self.api_key = config.AI["API_KEY"]
        self.api_url = config.AI.get("API_URL", "https://api.x.ai/v1")
        
        # Rate limiting
        self.api_calls_today = 0
        self.api_call_timestamps = []
        self.last_day_reset = datetime.now().date()
        
        # Ensure directories exist
        os.makedirs("cache/memes", exist_ok=True)
    
    def generate_meme(self, event):
        """Generate a meme image for a blockchain event.
        
        Args:
            event: Blockchain event data
            
        Returns:
            dict: Object with meme data including image URL
        """
        try:
            # Create a cache key
            cache_key = f"meme_{hashlib.md5(str(event).encode()).hexdigest()}"
            
            # Check if we have this in cache
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("Using cached meme")
                return cached_result
            
            # Get event category and data
            event_category = event.get('event_category', 'unknown')
            event_type = event.get('type', 'unknown')
            
            # Create prompt for image generation
            prompt = self._create_meme_prompt(event)
            
            # Call X.AI image generation API
            image_url = self._generate_image(prompt)
            
            if not image_url:
                logger.warning("Failed to generate meme image, using fallback")
                # Fallback to a default meme template
                image_url = "https://via.placeholder.com/800x450?text=Blockchain+Event"
            
            # Create title and message for the meme
            title, message = self._create_meme_text(event)
            
            # Create meme result
            result = {
                "title": title,
                "message": message,
                "image_url": image_url,
                "prompt": prompt,
                "event_type": event_type,
                "event_category": event_category,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            return result
        except Exception as e:
            logger.error(f"Error generating meme: {str(e)}")
            # Fallback result
            return {
                "title": "Blockchain Event",
                "message": "A blockchain event occurred.",
                "image_url": "https://via.placeholder.com/800x450?text=Fallback+Meme",
                "source": "error_fallback",
                "timestamp": datetime.now().isoformat()
            }

    def _create_meme_prompt(self, event):
        """Create a prompt for meme image generation based on the event.
        
        Args:
            event: Blockchain event data
            
        Returns:
            str: Prompt for image generation
        """
        try:
            event_category = event.get('event_category', 'unknown')
            event_type = event.get('type', 'unknown')
            
            # Base components that can be used in different meme prompts
            components = {
                "characters": ["crypto bro", "diamond hands investor", "scared trader", "moon boy", "crypto chad", "wojak", "pepe the frog"],
                "settings": ["trading desk", "moon surface", "yacht", "lambo", "crypto conference", "to the moon", "rocket ship"],
                "emotions": ["excited", "scared", "confused", "celebrating", "crying", "shocked"],
                "styles": ["meme style", "internet meme", "crypto meme", "dank meme", "retro pixel art", "vaporwave", "4chan style", "reddit meme"]
            }
            
            # Select random components
            character = random.choice(components["characters"])
            setting = random.choice(components["settings"])
            emotion = random.choice(components["emotions"])
            style = random.choice(components["styles"])
            
            # Create base prompt
            base_prompt = f"A {emotion} {character} in a {setting}, {style}, high quality"
            
            # Add event-specific details
            if event_type == "token_deposit" or event_type == "token_withdrawal":
                token_name = event.get('token_name', 'crypto token')
                action = "depositing" if event_type == "token_deposit" else "withdrawing"
                prompt = f"{base_prompt}, {action} {token_name}, blockchain transaction, funny crypto meme"
                
            elif event_type == "coin_deposit" or event_type == "coin_withdrawal":
                amount = event.get('amount_apt', "some coins")
                action = "receiving" if event_type == "coin_deposit" else "sending"
                prompt = f"{base_prompt}, {action} {amount} APT coins, cryptocurrency transaction, funny crypto meme"
                
            elif event_type == "large_transaction":
                amount = event.get('amount_apt', "large amount")
                prompt = f"{base_prompt}, transferring {amount} APT, whale transaction, big money moves, funny crypto meme"
                
            elif event_type == "nft_sale":
                token_name = event.get('token_name', 'NFT')
                amount = event.get('amount_apt', "some APT")
                prompt = f"{base_prompt}, buying {token_name} NFT for {amount} APT, NFT purchase, digital art, funny crypto meme"
                
            elif event_type == "liquidity_change":
                pool = event.get('pool_name', 'crypto pool')
                action = event.get('action', 'changing')
                prompt = f"{base_prompt}, {action} liquidity in {pool} DeFi pool, crypto trading, funny crypto meme"
                
            elif event_type == "price_movement":
                token = event.get('token_name', 'crypto')
                direction = event.get('direction', 'moving')
                prompt = f"{base_prompt}, {token} price {direction}, crypto chart, trading graph, funny crypto meme"
                
            else:
                prompt = f"{base_prompt}, crypto blockchain event, transaction, funny crypto meme"
            
            # Add some randomization
            additions = [
                "photorealistic", "high detail", "highly detailed", "4k", "trending on social media", 
                "viral meme", "funny", "absurd", "ridiculous", "over-the-top"
            ]
            
            # Add 2-3 random additions
            for _ in range(random.randint(2, 3)):
                addition = random.choice(additions)
                if addition not in prompt:  # Avoid duplicates
                    prompt += f", {addition}"
            
            return prompt
        except Exception as e:
            logger.error(f"Error creating meme prompt: {str(e)}")
            return "funny crypto meme, blockchain event, viral internet meme"
    
    def _create_meme_text(self, event):
        """Create title and message for a meme based on blockchain event.
        
        Args:
            event: Blockchain event data
            
        Returns:
            tuple: (title, message) for the meme
        """
        event_type = event.get('type', 'unknown')
        event_category = event.get('event_category', 'unknown')
        
        # Default title and message
        title = "Blockchain Update"
        message = "Something happened on the blockchain!"
        
        # Create specific messaging based on event type
        if event_type == "token_deposit":
            token_name = event.get('token_name', 'Unknown Token')
            title = f"TOKEN DEPOSIT DETECTED!!! 🚀🚀🚀"
            message = f"SOME1 JUS DEPOSITD {token_name}!!! BULLISH AF!!!1! 💰💰💰"
            
        elif event_type == "token_withdrawal":
            token_name = event.get('token_name', 'Unknown Token')
            title = f"OH NOES! TOKEN WITHDRAWAL!!! 😱"
            message = f"SUM PAPER HANDZ JUS WITHDREW {token_name}!!! NGMI 😤😤😤"
            
        elif event_type == "coin_deposit":
            amount = event.get('amount_apt', 'some')
            title = f"COIN DROP DETECTED!!! 💸💸💸"
            message = f"SUM1 JUST GOT {amount} APT!!! MEGA BULLISH!!! WEN LAMBO??? 🏎️🚀"
            
        elif event_type == "coin_withdrawal":
            amount = event.get('amount_apt', 'some')
            title = f"COIN DUMP ALERT!!! 📉📉📉"
            message = f"PAPERHANDS JUST DUMPED {amount} APT!!! HODL FRENZ!!! DIAMOND HANDZ ONLY!!! 💎🙌"
            
        elif event_type == "large_transaction":
            amount = event.get('amount_apt', 'HUGE')
            title = f"WHALE ALERT!!! 🐋🐋🐋"
            message = f"MEGA WHALE JUST MOVD {amount} APT!!! SUM1 KNOWS SUMTHIN!!! INSDIER TRADING??? 👀👀👀"
            
        elif event_type == "nft_sale":
            token_name = event.get('token_name', 'an NFT')
            amount = event.get('amount_apt', 'some')
            title = f"NFT FLIPD 4 PROFIT!!! 🖼️💰"
            message = f"SUM LUCKY DEGEN JUS SOLD {token_name} 4 {amount} APT!!! IM STILL POOR!!! 😭💸"
            
        elif event_type == "liquidity_change":
            pool = event.get('pool_name', 'some pool')
            action = event.get('action', 'changed')
            title = f"LP CHANGE DETECTED!!! 💦💦💦"
            message = f"SUM1 JUST {action} LIQUIDTY IN {pool}!!! DEFI SUMMER BACK???! 🌞🔥"
            
        elif event_type == "price_movement":
            token = event.get('token_name', 'something')
            direction = event.get('direction', 'moved')
            change = event.get('change_percentage', '??')
            title = f"{token} PRICE {direction.upper()}!!! {'🚀' if direction == 'up' else '📉'}"
            message = f"{token} JUST {direction} {change}%!!! {'TO THE MOON!!!' if direction == 'up' else 'BUY THE DIP!!!'} {'🚀🌕' if direction == 'up' else '💰🔥'}"
            
        return title, message
    
    def _generate_image(self, prompt):
        """Generate an image using X.AI's image generation API.
        
        Args:
            prompt: Text prompt for image generation
            
        Returns:
            str: URL to the generated image, or None if generation failed
        """
        try:
            # Check rate limits
            current_time = datetime.now()
            
            # Reset daily counter if it's a new day
            if current_time.date() != self.last_day_reset:
                self.last_day_reset = current_time.date()
                self.api_calls_today = 0
                logger.info("Resetting daily API call counter")
            
            # Check if we've exceeded daily limit
            max_daily_calls = self.config.AI.get("MAX_DAILY_CALLS", 100)
            if self.api_calls_today >= max_daily_calls:
                logger.warning(f"Daily API call limit exceeded: {self.api_calls_today}/{max_daily_calls}")
                return None
            
            # Check rate limit within the time period
            rate_limit_period = self.config.AI.get("RATE_LIMIT_PERIOD", 60)
            rate_limit_calls = self.config.AI.get("RATE_LIMIT_CALLS", 10)
            
            # Remove timestamps older than the rate limit period
            self.api_call_timestamps = [ts for ts in self.api_call_timestamps 
                                       if (current_time - ts).total_seconds() < rate_limit_period]
            
            # Check if we've exceeded the rate limit
            if len(self.api_call_timestamps) >= rate_limit_calls:
                # Find the oldest call in our window and calculate when we can make another request
                oldest_call = min(self.api_call_timestamps)
                wait_time = rate_limit_period - (current_time - oldest_call).total_seconds()
                logger.warning(f"Rate limit reached. Need to wait {wait_time:.1f} seconds for next API call")
                return None
            
            # Prepare the API request for image generation
            url = f"{self.api_url}/images/generations"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Based on X.AI image generation API documentation from the provided URL
            data = {
                "model": self.config.AI.get("IMAGE_MODEL", "dall-e-3"),  # Use model from config or default
                "prompt": prompt,
                "n": 1,  # Generate one image
                "size": "1024x1024",  # Standard size
                "quality": "standard",
                "style": "vivid",  # Other option is "natural"
                "response_format": "url"  # Get URL in response
            }
            
            # Make the API request with timeout
            logger.info("Making API request to X.AI for image generation...")
            logger.info(f"Prompt: {prompt}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)  # Longer timeout for images
            
            # Update rate limit tracking
            self.api_call_timestamps.append(current_time)
            self.api_calls_today += 1
            logger.info(f"API call count today: {self.api_calls_today}/{max_daily_calls}")
            
            # Check if the request was successful
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the image URL based on X.AI API response format
                if "data" in response_data and len(response_data["data"]) > 0:
                    image_url = response_data["data"][0]["url"]
                    logger.info(f"Successfully generated image: {image_url[:50]}...")
                    return image_url
                else:
                    logger.error("No image data in API response")
                    logger.error(f"Response: {response_data}")
                    return None
            else:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("API request for image generation timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error for image generation: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in image generation: {str(e)}")
            return None
    
    def _get_from_cache(self, key):
        """Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            object: Cached data or None if not found/expired
        """
        cache_file = f"cache/memes/{key}.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check if cache has expired
                ttl = self.config.AI.get("CACHE_DURATION", 3600)  # Default 1 hour
                timestamp = datetime.fromisoformat(data.get("timestamp", "2000-01-01T00:00:00"))
                age = (datetime.now() - timestamp).total_seconds()
                
                if age < ttl:
                    return data
            except Exception as e:
                logger.error(f"Error reading from cache: {str(e)}")
        
        return None
    
    def _save_to_cache(self, key, data):
        """Save item to cache.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        try:
            cache_file = f"cache/memes/{key}.json"
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}") 