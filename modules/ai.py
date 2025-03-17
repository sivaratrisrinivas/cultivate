# modules/ai.py
import json
import os
import requests
import random
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from utils.logger import get_logger
from utils.cache import Cache

# Define emoji pattern for removing emojis from text
emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F700-\U0001F77F"  # alchemical symbols
                           u"\U0001F780-\U0001F7FF"  # Geometric Shapes
                           u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                           u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                           u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                           u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                           u"\U00002702-\U000027B0"  # Dingbats
                           u"\U000024C2-\U0001F251" 
                           "]+", flags=re.UNICODE)

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
    
    def _call_ai_api(self, system_prompt, user_prompt):
        """Call the X.AI API with the given prompts.
        
        Args:
            system_prompt (str): System prompt for the AI
            user_prompt (str): User prompt for the AI
            
        Returns:
            str: Generated text from the AI, or None if an error occurred
        """
        try:
            import requests
            
            # Prepare the API request
            url = f"{self.config.AI['API_URL']}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.AI['API_KEY']}"
            }
            
            data = {
                "model": self.config.AI["MODEL"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.config.AI["TEMPERATURE"],
                "max_tokens": 500
            }
            
            # Make the API request with timeout
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            # Check if the request was successful
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the generated text
                if response_data.get("choices") and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"]
                else:
                    logger.error("No choices in API response")
                    return None
            else:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in _call_ai_api: {str(e)}")
            return None
    
    def generate_post(self, event):
        """Generate a social media post for a blockchain event.
        
        Args:
            event: A BlockchainEvent object
            
        Returns:
            dict: A social media post object with content and metadata
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
                "nft_event": [
                    "🖼️ NFT Alert: {token_name} from {collection_name} collection {action} on Aptos! {additional_context}",
                    "🎨 NFT Activity: {token_name} just {action} on Aptos. {impact_statement}",
                    "NFT Update: {token_name} from {collection_name} {action}. {market_insight}"
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
            
            # Map event type to template category
            template_category = "generic_event"
            if "token" in event_type.lower():
                template_category = "token_event"
            elif "nft" in event_type.lower():
                template_category = "nft_event"
            elif "transaction" in event_type.lower():
                template_category = "transaction_event"
            
            # Select template based on event type and importance
            template_list = templates.get(template_category, templates["generic_event"])
            template_index = min(int(importance * len(template_list)), len(template_list) - 1)
            template = template_list[template_index]
            
            # Format placeholders
            formatted_template = self._format_template(template, event_data, event_type)
            
            # Use LLM to enhance the post
            enhanced_post = self._enhance_post_with_llm(formatted_template, context)
            
            # Create hashtags
            hashtags = self._generate_hashtags(event_type)
            
            # Ensure the post is not too long with hashtags
            max_content_length = 280 - len(" ".join(hashtags)) - 1  # -1 for space
            if len(enhanced_post) > max_content_length:
                enhanced_post = enhanced_post[:max_content_length-3] + "..."
            
            # Combine post with hashtags
            final_post = f"{enhanced_post} {' '.join(hashtags)}"
            
            logger.info(f"Generated post: {final_post[:100]}...")
            
            # Return post object
            return {
                "content": final_post,
                "event_reference": f"{event_type}_{datetime.now().isoformat()}",
                "source_event": event.to_dict() if hasattr(event, 'to_dict') else event,
                "hashtags": hashtags,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            # Fallback post
            fallback_post = f"Something interesting just happened on Aptos blockchain! #{event_type.replace('_', '')}"
            return {
                "content": fallback_post,
                "event_reference": f"{event_type}_{datetime.now().isoformat()}",
                "source_event": event.to_dict() if hasattr(event, 'to_dict') else event,
                "hashtags": ["#Aptos", "#Blockchain"],
                "generated_at": datetime.now().isoformat()
            }
    
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
                "market_insight": "",
                "collection_name": event_data.get("collection_name", "Unknown Collection")
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
            7. DO NOT include hashtags (like #Aptos or #NFT) in your messages
            
            For NFT events, express excitement about the artwork, collection, or trading activity.
            For coin transfers, comment on the significance of the amount or potential market impact.
            For new collections, show enthusiasm about new creative projects on Aptos.
            
            Keep your responses concise (2-3 sentences) but conversational. Include relevant links when available.
            DO NOT fabricate information not provided in the event data.
            DO NOT include hashtags in your response.
            """
            
            user_prompt = f"""
            EVENT INFORMATION:
            - Type: {context['event_type']}
            - Data: {json.dumps(context['event_data'], indent=2)}
            - Importance (0-1): {context['importance']}
            - Timestamp: {context['timestamp']}
            
            BASE POST:
            {base_post}
            
            ENHANCED POST:
            """
            
            # Get response from LLM using the Grok API
            response = self._call_ai_api(system_prompt, user_prompt)
            
            # Extract enhanced post
            if response:
                enhanced_post = response.strip()
                
                # Ensure post is not too long
                if len(enhanced_post) > 280:
                    enhanced_post = enhanced_post[:277] + "..."
                    
                return enhanced_post
            else:
                logger.warning("Failed to get response from LLM, using base post")
                return base_post
            
        except Exception as e:
            logger.error(f"Error enhancing post with LLM: {str(e)}")
            return base_post
    
    def generate_meme(self, event):
        """Generate a meme based on a blockchain event."""
        event_type = event.event_type
        
        # Generate meme text using Grok
        system_prompt = "You are a meme creator specializing in blockchain humor."
        user_prompt = f"Create a funny meme about {event_type} on the Aptos blockchain. Format: TOP TEXT | BOTTOM TEXT"
        
        meme_text = self._call_ai_api(system_prompt, user_prompt)
        
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
            "You are Cultivate, an AI assistant specializing in the Aptos blockchain ecosystem. "
            "Provide accurate, helpful information about Aptos, focusing on technical details, "
            "ecosystem updates, and how-to guidance. Your responses should be friendly and conversational, "
            "as if you're chatting with users in a Discord server. Include relevant examples when helpful "
            "and explain technical concepts in an accessible way. If you're unsure about something, "
            "acknowledge it rather than providing potentially incorrect information. "
            "For questions about recent events or current statistics, note that your knowledge may not "
            "include the very latest updates."
        )
        
        answer = self._call_ai_api(system_prompt, question)
        
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
        
        result = self._call_ai_api(system_prompt, user_prompt)
        
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
        # Base hashtags for all posts
        base_hashtags = ["#Aptos", "#Web3"]
        
        # Event-specific hashtags
        if "nft" in event_type.lower():
            specific_hashtags = ["#NFT", "#DigitalArt", "#AptoNFTs"]
        elif "token" in event_type.lower():
            specific_hashtags = ["#Crypto", "#DeFi", "#AptosEcosystem"]
        elif "transaction" in event_type.lower():
            specific_hashtags = ["#Blockchain", "#Crypto", "#AptosNetwork"]
        elif "contract" in event_type.lower():
            specific_hashtags = ["#SmartContracts", "#BuildOnAptos"]
        else:
            specific_hashtags = ["#Blockchain", "#Move"]
        
        # Select 2 random specific hashtags to keep it concise
        selected = random.sample(specific_hashtags, min(2, len(specific_hashtags)))
        
        return base_hashtags + selected
    
    def _format_post(self, content, hashtags):
        """Format content without hashtags ensuring character limit."""
        # Don't include hashtags as per user request
        max_content_length = 280
        
        if len(content) > max_content_length:
            content = content[:max_content_length-3] + "..."
        
        return content
    
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
        """Generate insights for a blockchain event.
        
        Args:
            event (dict): Blockchain event data
            
        Returns:
            dict: Generated insights including title, message, and conversation starter
        """
        logger.info(f"Generating insights for event: {event.get('event_category', 'unknown')}")
        
        # Default insights in case AI generation fails
        default_insights = {
            "title": self._get_default_title(event),
            "message": self._get_default_message(event),
            "conversation_starter": "What do you think about this event?",
            "analysis": "No detailed analysis available."
        }
        
        try:
            # Skip AI for test events if configured to do so
            if event.get('is_test', False) and not self.config.AI.get("PROCESS_TEST_EVENTS", False):
                logger.info("Skipping AI processing for test event")
                return default_insights
                
            logger.info("Calling X.AI API to generate insights")
            
            # Prepare system prompt
            system_prompt = """You are a friendly and knowledgeable blockchain community manager for Aptos.
Your job is to engage with users about blockchain events in a conversational way.
Be casual, direct, and use simple language. DO NOT use emojis.
Keep your messages concise, interactive, and witty.
DO NOT include hashtags (like #Aptos or #NFT) in your messages.
Focus on explaining what happened in the event and why it might be interesting or important.
End with a question to encourage discussion."""
            
            # Prepare user prompt with event details
            user_prompt = f"Here's a blockchain event on Aptos:\n\nEvent Type: {event.get('event_category', 'Unknown')}\n"
            
            # Add relevant event details based on event type
            if event.get('event_category') == 'token_deposit' or event.get('event_category') == 'token_withdrawal':
                user_prompt += f"Token: {event.get('token_name', 'Unknown')}\n"
                user_prompt += f"Collection: {event.get('collection_name', 'Unknown')}\n"
                user_prompt += f"Account: {event.get('account', 'Unknown')}\n"
                
            elif event.get('event_category') == 'coin_transfer':
                user_prompt += f"Amount: {event.get('amount_apt', 0)} APT\n"
                user_prompt += f"From: {event.get('from_account', 'Unknown')}\n"
                user_prompt += f"To: {event.get('to_account', 'Unknown')}\n"
                
            elif event.get('event_category') == 'nft_sale':
                user_prompt += f"NFT: {event.get('token_name', 'Unknown')}\n"
                user_prompt += f"Collection: {event.get('collection_name', 'Unknown')}\n"
                user_prompt += f"Price: {event.get('amount_apt', 0)} APT\n"
                
            elif event.get('event_category') == 'liquidity_change':
                user_prompt += f"Pool: {event.get('pool_name', 'Unknown')}\n"
                user_prompt += f"Change: {event.get('change_percentage', 0)}%\n"
                user_prompt += f"Action: {event.get('action', 'Unknown')}\n"
                
            elif event.get('event_category') == 'price_movement':
                user_prompt += f"Token: {event.get('token_name', 'Unknown')}\n"
                user_prompt += f"Change: {event.get('change_percentage', 0)}%\n"
                user_prompt += f"Direction: {event.get('direction', 'Unknown')}\n"
                
            # Add description if available
            if event.get('description'):
                user_prompt += f"\nDescription: {event.get('description')}\n"
                
            # Add transaction link if available
            if event.get('transaction_url'):
                user_prompt += f"\nTransaction: {event.get('transaction_url')}\n"
                
            user_prompt += "\nPlease generate:\n1. A short title for this event (max 50 chars)\n2. A concise, witty message about this event without emojis (max 280 chars)\n3. A conversation starter question\n4. A brief analysis of what this might mean"
            
            # Call the AI API
            logger.info(f"Making API request to X.AI with model: {self.config.AI['MODEL']}")
            response = self._call_ai_api(system_prompt, user_prompt)
            
            if not response:
                logger.warning("Failed to get response from X.AI API, using default insights")
                return default_insights
                
            logger.info("Successfully received response from X.AI API")
            
            # Parse the response
            try:
                lines = response.strip().split('\n')
                
                # Extract title, message, conversation starter, and analysis
                title = ""
                message = ""
                conversation_starter = ""
                analysis = ""
                
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("Title:"):
                        current_section = "title"
                        title = line[6:].strip()
                    elif line.startswith("Message:"):
                        current_section = "message"
                        message = line[8:].strip()
                    elif line.startswith("Conversation starter:"):
                        current_section = "conversation_starter"
                        conversation_starter = line[21:].strip()
                    elif line.startswith("Analysis:"):
                        current_section = "analysis"
                        analysis = line[9:].strip()
                    elif current_section:
                        if current_section == "title":
                            title += " " + line
                        elif current_section == "message":
                            message += " " + line
                        elif current_section == "conversation_starter":
                            conversation_starter += " " + line
                        elif current_section == "analysis":
                            analysis += " " + line
                
                # Ensure we have all required fields
                if not title:
                    title = default_insights["title"]
                if not message:
                    message = default_insights["message"]
                if not conversation_starter:
                    conversation_starter = default_insights["conversation_starter"]
                if not analysis:
                    analysis = default_insights["analysis"]
                    
                # Truncate if needed
                title = title[:50]
                message = message[:280]
                
                # Remove any emojis that might have slipped through
                message = emoji_pattern.sub(r'', message)
                
                insights = {
                    "title": title,
                    "message": message,
                    "conversation_starter": conversation_starter,
                    "analysis": analysis
                }
                
                logger.info(f"Successfully generated message: {message[:70]}...")
                return insights
                
            except Exception as parsing_error:
                logger.error(f"Error parsing AI response: {str(parsing_error)}")
                return default_insights
                
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return default_insights

    def _get_default_title(self, event):
        """Get a default title for an event if AI generation fails.
        
        Args:
            event (dict): Blockchain event data
            
        Returns:
            str: Default title for the event
        """
        event_category = event.get('event_category', 'unknown')
        
        if event_category == 'token_deposit':
            token_name = event.get('token_name', 'Unknown Token')
            return f"Token Deposit: {token_name}"
            
        elif event_category == 'token_withdrawal':
            token_name = event.get('token_name', 'Unknown Token')
            return f"Token Withdrawal: {token_name}"
            
        elif event_category == 'coin_transfer':
            amount = event.get('amount_apt', 0)
            return f"Coin Transfer: {amount:.2f} APT"
            
        elif event_category == 'nft_sale':
            token_name = event.get('token_name', 'Unknown NFT')
            amount = event.get('amount_apt', 0)
            return f"NFT Sale: {token_name} for {amount:.2f} APT"
            
        elif event_category == 'liquidity_change':
            pool = event.get('pool_name', 'Unknown Pool')
            return f"Liquidity Change in {pool} Pool"
            
        elif event_category == 'price_movement':
            token = event.get('token_name', 'Unknown Token')
            return f"Price Movement: {token}"
            
        elif event_category == 'large_transaction':
            amount = event.get('amount_apt', 0)
            return f"Large Transaction: {amount:.2f} APT"
            
        else:
            return f"Blockchain Event: {event_category.replace('_', ' ').title()}"
    
    def _get_default_message(self, event):
        """Get a default message for an event if AI generation fails.
        
        Args:
            event (dict): Blockchain event data
            
        Returns:
            str: Default message for the event
        """
        # Use the description if available
        if event.get('description'):
            return event.get('description')
            
        event_category = event.get('event_category', 'unknown')
        
        if event_category == 'token_deposit':
            token_name = event.get('token_name', 'Unknown Token')
            account = event.get('account', 'Unknown Account')
            short_account = account[:6] + '...' + account[-4:] if len(account) > 10 else account
            return f"A token deposit of {token_name} was detected to account {short_account}."
            
        elif event_category == 'token_withdrawal':
            token_name = event.get('token_name', 'Unknown Token')
            account = event.get('account', 'Unknown Account')
            short_account = account[:6] + '...' + account[-4:] if len(account) > 10 else account
            return f"A token withdrawal of {token_name} was detected from account {short_account}."
            
        elif event_category == 'coin_transfer':
            amount = event.get('amount_apt', 0)
            from_account = event.get('from_account', 'Unknown Account')
            to_account = event.get('to_account', 'Unknown Account')
            short_from = from_account[:6] + '...' + from_account[-4:] if len(from_account) > 10 else from_account
            short_to = to_account[:6] + '...' + to_account[-4:] if len(to_account) > 10 else to_account
            return f"A coin transfer of {amount:.2f} APT was detected from {short_from} to {short_to}."
            
        elif event_category == 'nft_sale':
            token_name = event.get('token_name', 'Unknown NFT')
            amount = event.get('amount_apt', 0)
            return f"An NFT sale of {token_name} for {amount:.2f} APT was detected."
            
        elif event_category == 'liquidity_change':
            pool = event.get('pool_name', 'Unknown Pool')
            change = event.get('change_percentage', 0)
            action = "added to" if change > 0 else "removed from"
            return f"Liquidity was {action} the {pool} pool by {abs(change):.2f}%."
            
        elif event_category == 'price_movement':
            token = event.get('token_name', 'Unknown Token')
            change = event.get('change_percentage', 0)
            direction = "up" if change > 0 else "down"
            return f"The price of {token} moved {direction} by {abs(change):.2f}% in the last hour."
            
        elif event_category == 'large_transaction':
            amount = event.get('amount_apt', 0)
            return f"A large transaction of {amount:.2f} APT was detected."
            
        else:
            return f"A blockchain event of type {event_category.replace('_', ' ').title()} was detected."
