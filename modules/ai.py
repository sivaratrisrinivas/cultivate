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
            
            logger.info(f"Making API request to X.AI with model: {self.model}")
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # Increased timeout from 10 to 30 seconds
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("Successfully received response from X.AI API")
            
            # Extract the generated text
            return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
        except requests.exceptions.Timeout:
            logger.error("Grok API request timed out after 30 seconds")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Grok API request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Grok API: {str(e)}")
            return None
    
    def generate_post(self, event):
        """Generate a social media post for a blockchain event.
        
        Args:
            event: A BlockchainEvent object
            
        Returns:
            str: A social media post
        """
        try:
            logger.info(f"Generating post for event: {event.event_type}")
            
            # Extract key information from the event
            event_type = event.event_type
            event_data = event.data
            importance = event.importance_score
            
            # Create a detailed context for the LLM
            context = {
                "event_type": event_type,
                "event_data": event_data,
                "importance": importance,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "blockchain": "Aptos"
            }
            
            # Define templates based on event type
            templates = {
                "token_event": [
                    "🚨 Token Alert: {amount} {token_name} ({token_symbol}) {action} on Aptos! {additional_context}",
                    "💰 {amount} {token_name} just {action} on Aptos. {impact_statement}",
                    "Token Movement: {amount} {token_name} {action}. {market_insight}"
                ],
                "transaction_event": [
                    "📊 Significant transaction on Aptos: {tx_description}. {impact_statement}",
                    "🔄 Transaction Alert: {tx_description} on Aptos. {additional_context}",
                    "New transaction worth noting: {tx_description}. {market_insight}"
                ],
                "generic_event": [
                    "🔔 Aptos Update: {event_description}. {additional_context}",
                    "📢 Notable activity on Aptos: {event_description}. {impact_statement}",
                    "Aptos Blockchain Alert: {event_description}. {market_insight}"
                ]
            }
            
            # Select template based on event type and importance
            template_list = templates.get(event_type, templates["generic_event"])
            template_index = min(int(importance * len(template_list)), len(template_list) - 1)
            template = template_list[template_index]
            
            # Format placeholders
            formatted_template = self._format_template(template, event_data, event_type)
            
            # Use LLM to enhance the post
            enhanced_post = self._enhance_post_with_llm(formatted_template, context)
            
            logger.info(f"Generated post: {enhanced_post[:100]}...")
            return enhanced_post
            
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            return f"Something interesting just happened on Aptos blockchain! #{event.event_type}"
    
    def _format_template(self, template, event_data, event_type):
        """Format template with event data."""
        try:
            # Extract common fields
            placeholders = {
                "token_name": event_data.get("token_name", "tokens"),
                "token_symbol": event_data.get("token_symbol", ""),
                "amount": self._format_amount(event_data.get("amount", 0)),
                "action": event_data.get("action", "transferred"),
                "tx_description": self._create_tx_description(event_data),
                "event_description": self._create_event_description(event_data, event_type),
                "additional_context": "",
                "impact_statement": "",
                "market_insight": ""
            }
            
            # Return formatted template
            return template.format(**placeholders)
            
        except Exception as e:
            logger.error(f"Error formatting template: {str(e)}")
            return template
    
    def _format_amount(self, amount):
        """Format amount with appropriate units."""
        try:
            amount = float(amount)
            if amount >= 1_000_000:
                return f"{amount/1_000_000:.2f}M"
            elif amount >= 1_000:
                return f"{amount/1_000:.2f}K"
            else:
                return f"{amount:.2f}"
        except:
            return str(amount)
    
    def _create_tx_description(self, event_data):
        """Create a description for a transaction event."""
        sender = event_data.get("sender", "Unknown")
        receiver = event_data.get("receiver", "")
        amount = event_data.get("amount", "")
        gas = event_data.get("gas_used", "")
        
        if receiver and amount:
            return f"{self._format_amount(amount)} transferred from {self._shorten_address(sender)} to {self._shorten_address(receiver)}"
        elif gas:
            return f"Transaction by {self._shorten_address(sender)} using {gas} gas"
        else:
            return f"Transaction by {self._shorten_address(sender)}"
    
    def _create_event_description(self, event_data, event_type):
        """Create a description for a generic event."""
        if event_type == "token_event":
            token = event_data.get("token_name", "tokens")
            action = event_data.get("action", "transferred")
            amount = event_data.get("amount", "")
            return f"{self._format_amount(amount)} {token} {action}"
        elif "description" in event_data:
            return event_data["description"]
        else:
            return f"New {event_type.replace('_', ' ')}"
    
    def _shorten_address(self, address):
        """Shorten blockchain address for readability."""
        if not address or len(address) < 10:
            return address
        return address[:6] + "..." + address[-4:]
    
    def _enhance_post_with_llm(self, base_post, context):
        """Use LLM to enhance the post with additional context and insights."""
        try:
            # Create prompt for LLM
            prompt = f"""
            You are a blockchain analyst creating informative and engaging social media posts about events on the Aptos blockchain.
            
            EVENT INFORMATION:
            - Type: {context['event_type']}
            - Data: {json.dumps(context['event_data'], indent=2)}
            - Importance (0-1): {context['importance']}
            - Timestamp: {context['timestamp']}
            
            TASK:
            Enhance the following base post by adding relevant context, impact analysis, and market insights.
            Make it informative, engaging, and suitable for crypto enthusiasts.
            Keep it concise (max 280 characters) and add relevant hashtags.
            Avoid speculation and maintain a neutral tone.
            
            BASE POST:
            {base_post}
            
            ENHANCED POST:
            """
            
            # Get response from LLM
            response = self.llm.generate_text(prompt, max_tokens=300)
            
            # Extract enhanced post
            enhanced_post = response.strip()
            
            # Ensure post is not too long
            if len(enhanced_post) > 280:
                enhanced_post = enhanced_post[:277] + "..."
            
            return enhanced_post
            
        except Exception as e:
            logger.error(f"Error enhancing post with LLM: {str(e)}")
            return base_post
    
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

    def generate_insights(self, event):
        """Generate AI insights from blockchain events.
        
        Args:
            event (dict): Enriched blockchain event data
            
        Returns:
            dict: Generated insights including message, title, and analysis
        """
        logger.info(f"Generating insights for event: {event.get('event_category', 'unknown')}")
        
        # Extract key information from the event
        event_category = event.get("event_category", "other")
        description = event.get("description", "Blockchain event")
        account = event.get("account", "Unknown account")
        account_url = event.get("account_url", "")
        transaction_url = event.get("transaction_url", "")
        timestamp = event.get("timestamp", datetime.now().isoformat())
        
        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            formatted_time = timestamp
            
        # Create context for AI prompt based on event type
        context = {
            "event_type": event_category,
            "description": description,
            "account": account,
            "timestamp": formatted_time,
            "transaction_url": transaction_url,
            "account_url": account_url,
        }
        
        # Add token-specific information if available
        if "token_name" in event:
            context["token_name"] = event["token_name"]
            context["collection_name"] = event.get("collection_name", "Unknown Collection")
            
        # Add amount information for coin transfers
        if "amount_apt" in event:
            context["amount"] = f"{event['amount_apt']:.8f} APT"
            
        # Create system prompt for the AI
        system_prompt = """
        You are Cultivate, a friendly and personable Discord bot that monitors the Aptos blockchain. 
        Your personality is helpful, enthusiastic, and slightly witty. You speak directly to users as if having a conversation.
        
        When reporting blockchain events, follow these guidelines:
        1. Use a conversational tone like you're chatting with friends in the Discord server
        2. Address the users directly using "you" and "your" (e.g., "Hey everyone! Thought you'd want to know...")
        3. Ask occasional questions to engage users (e.g., "What do you think about this transaction?")
        4. Express opinions and reactions to events (e.g., "This looks like an interesting NFT transfer!")
        5. Use casual language, contractions, and occasional slang where appropriate
        6. Include relevant emojis to make your messages more engaging
        
        For NFT events, express excitement about the artwork, collection, or trading activity.
        For coin transfers, comment on the significance of the amount or potential market impact.
        For new collections, show enthusiasm about new creative projects on Aptos.
        
        Keep your responses concise (2-3 sentences) but conversational. Include relevant links when available.
        DO NOT fabricate information not provided in the event data.
        """
        
        # Create user prompt with event details
        user_prompt = f"""
        Please generate a Discord notification for this Aptos blockchain event:
        
        Event Type: {context['event_type']}
        Description: {context['description']}
        Account: {context['account']}
        Time: {context['timestamp']}
        
        """
        
        # Add token details if available
        if "token_name" in context:
            user_prompt += f"""
            Token Name: {context['token_name']}
            Collection: {context['collection_name']}
            """
            
        # Add amount for coin transfers
        if "amount" in context:
            user_prompt += f"Amount: {context['amount']}\n"
            
        # Add links if available
        if transaction_url:
            user_prompt += f"Transaction URL: {transaction_url}\n"
        if account_url:
            user_prompt += f"Account URL: {account_url}\n"
            
        # Call AI API to generate content
        try:
            response = self._call_grok_api(system_prompt, user_prompt)
            message = response.get("content", "")
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            # Fallback message if AI API fails
            if event_category == "nft_transfer":
                message = f"🖼️ NFT Transfer Alert! {description}. Check it out at {transaction_url}"
            elif event_category == "nft_mint":
                message = f"🎨 New NFT Minted! {description}. View transaction: {transaction_url}"
            elif event_category == "coin_transfer":
                message = f"💰 Coin Transfer: {description}. Details: {transaction_url}"
            elif event_category == "collection_creation":
                message = f"🚀 New Collection Created! {description}. Explore: {transaction_url}"
            else:
                message = f"📊 Aptos Blockchain Update: {description}. More info: {transaction_url}"
        
        # Generate a title for the notification
        if event_category == "nft_transfer":
            title = "NFT Transfer Detected"
        elif event_category == "nft_mint":
            title = "New NFT Minted"
        elif event_category == "coin_transfer":
            title = "Coin Transfer Alert"
        elif event_category == "collection_creation":
            title = "New Collection Created"
        else:
            title = "Aptos Blockchain Update"
            
        # Create the insights object
        insights = {
            "message": message,
            "title": title,
            "raw_event": event,
            "generated_at": datetime.now().isoformat(),
            "importance_score": event.get("importance_score", 0.5),
            "links": {
                "transaction": transaction_url,
                "account": account_url
            }
        }
        
        # Add a brief analysis
        insights["analysis"] = self._generate_brief_analysis(event)
        
        return insights
        
    def _generate_brief_analysis(self, event):
        """Generate a brief analysis of the event for internal use."""
        event_category = event.get("event_category", "other")
        
        if event_category == "nft_transfer":
            return "What do you think about this NFT movement? Could be a collector or maybe a new marketplace trend!"
        elif event_category == "nft_mint":
            return "Fresh NFTs are always exciting! Anyone planning to check out this collection?"
        elif event_category == "coin_transfer":
            amount = event.get("amount_apt", 0)
            if amount > 1000:
                return "That's a significant amount of APT moving around! What could it mean for the market?"
            elif amount > 100:
                return "Decent amount of APT on the move. Anyone have thoughts on this transaction?"
            else:
                return "Small transactions add up! What are you all trading today?"
        elif event_category == "collection_creation":
            return "New collections are the lifeblood of the NFT space! Anyone planning to mint from this one?"
        else:
            return "What do you all think about this blockchain activity? Anything interesting catch your eye?"
