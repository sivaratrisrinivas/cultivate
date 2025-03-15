# modules/discord_bot.py
import discord
import os
import asyncio
import random
import re
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from utils.logger import get_logger

logger = get_logger("discord_bot")

class DiscordBot:
    """Discord bot for social media management."""
    
    def __init__(self, config, ai_module):
        """Initialize the Discord bot."""
        self.config = config
        self.ai_module = ai_module
        self.blockchain_monitor = None
        
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
    
    def set_blockchain_monitor(self, blockchain_monitor):
        """Set the blockchain monitor reference."""
        self.blockchain_monitor = blockchain_monitor
    
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
            
            # Process commands first
            await self.bot.process_commands(message)
            
            # Then handle potential questions
            await self._handle_potential_question(message)
        
        # Register commands
        self._register_commands()
    
    def _register_commands(self):
        """Register bot commands."""
        @self.bot.command(name='aptos')
        async def aptos_info(ctx):
            """Get information about Aptos blockchain."""
            response = self.ai_module.get_answer("what is aptos")
            await ctx.send(response["answer"])
        
        @self.bot.command(name='blockchain_info')
        async def blockchain_info(ctx):
            """Get information about the blockchain monitor."""
            if not self.blockchain_monitor:
                await ctx.send("⚠️ Blockchain monitor not available")
                return
                
            event_handles_count = len(self.blockchain_monitor.event_handles) if hasattr(self.blockchain_monitor, 'event_handles') else 0
            await ctx.send(f"🔍 Monitoring {event_handles_count} event handles on Aptos blockchain")
        
        @self.bot.command(name='monitor')
        async def monitor_command(ctx, action=None, item_type=None, *, value=None):
            """Monitor a specific account, token, or collection."""
            if not self.blockchain_monitor:
                await ctx.send("⚠️ Blockchain monitor not available")
                return
                
            # Debug information
            await ctx.send(f"Debug: Blockchain monitor type: {type(self.blockchain_monitor).__name__}")
            
            if not action:
                await ctx.send("Please specify an action: add, remove, or list")
                return
                
            action = action.lower()
            
            # List all monitored items
            if action == "list":
                try:
                    accounts = getattr(self.blockchain_monitor, 'monitored_accounts', [])
                    tokens = getattr(self.blockchain_monitor, 'monitored_tokens', [])
                    collections = getattr(self.blockchain_monitor, 'monitored_collections', [])
                    
                    embed = discord.Embed(
                        title="🔍 Monitored Items",
                        description="Here are the items you're currently monitoring:",
                        color=0x3498db
                    )
                    
                    if accounts:
                        accounts_str = "\n".join([f"• `{self._format_address(a)}`" for a in accounts])
                        embed.add_field(name="📝 Accounts", value=accounts_str or "None", inline=False)
                    else:
                        embed.add_field(name="📝 Accounts", value="None", inline=False)
                        
                    if tokens:
                        tokens_str = "\n".join([f"• `{t}`" for t in tokens])
                        embed.add_field(name="🪙 Tokens", value=tokens_str or "None", inline=False)
                    else:
                        embed.add_field(name="🪙 Tokens", value="None", inline=False)
                        
                    if collections:
                        collections_str = "\n".join([f"• `{c}`" for c in collections])
                        embed.add_field(name="🖼️ Collections", value=collections_str or "None", inline=False)
                    else:
                        embed.add_field(name="🖼️ Collections", value="None", inline=False)
                        
                    embed.set_footer(text="You'll receive notifications for events related to these items")
                    await ctx.send(embed=embed)
                except Exception as e:
                    await ctx.send(f"⚠️ Error listing monitored items: {str(e)}")
                return
                
            # Add or remove items
            if not item_type or not value:
                await ctx.send("Please specify both item type (account, token, collection) and value")
                return
                
            item_type = item_type.lower()
            
            if item_type not in ["account", "token", "collection"]:
                await ctx.send("Item type must be one of: account, token, collection")
                return
                
            # Handle add action
            if action == "add":
                if item_type == "account":
                    if value not in self.blockchain_monitor.monitored_accounts:
                        self.blockchain_monitor.monitored_accounts.append(value)
                        await ctx.send(f"✅ Now monitoring account: `{self._format_address(value)}`")
                    else:
                        await ctx.send(f"Account `{self._format_address(value)}` is already being monitored")
                        
                elif item_type == "token":
                    if value not in self.blockchain_monitor.monitored_tokens:
                        self.blockchain_monitor.monitored_tokens.append(value)
                        await ctx.send(f"✅ Now monitoring token: `{value}`")
                    else:
                        await ctx.send(f"Token `{value}` is already being monitored")
                        
                elif item_type == "collection":
                    if value not in self.blockchain_monitor.monitored_collections:
                        self.blockchain_monitor.monitored_collections.append(value)
                        await ctx.send(f"✅ Now monitoring collection: `{value}`")
                    else:
                        await ctx.send(f"Collection `{value}` is already being monitored")
                        
            # Handle remove action
            elif action == "remove":
                if item_type == "account":
                    if value in self.blockchain_monitor.monitored_accounts:
                        self.blockchain_monitor.monitored_accounts.remove(value)
                        await ctx.send(f"❌ Stopped monitoring account: `{self._format_address(value)}`")
                    else:
                        await ctx.send(f"Account `{self._format_address(value)}` is not being monitored")
                        
                elif item_type == "token":
                    if value in self.blockchain_monitor.monitored_tokens:
                        self.blockchain_monitor.monitored_tokens.remove(value)
                        await ctx.send(f"❌ Stopped monitoring token: `{value}`")
                    else:
                        await ctx.send(f"Token `{value}` is not being monitored")
                        
                elif item_type == "collection":
                    if value in self.blockchain_monitor.monitored_collections:
                        self.blockchain_monitor.monitored_collections.remove(value)
                        await ctx.send(f"❌ Stopped monitoring collection: `{value}`")
                    else:
                        await ctx.send(f"Collection `{value}` is not being monitored")
            else:
                await ctx.send("Action must be one of: add, remove, list")
                
        @self.bot.command(name='bot_help')
        async def bot_help_command(ctx):
            """Show help information."""
            help_text = (
                "**Aptos Social Manager Bot**\n\n"
                "I monitor the Aptos blockchain and post updates about significant events. "
                "I can also answer questions about Aptos!\n\n"
                "**Commands:**\n"
                f"- `{self.config.DISCORD['PREFIX']}aptos` - Get information about Aptos blockchain\n"
                f"- `{self.config.DISCORD['PREFIX']}blockchain_info` - Get information about the blockchain monitor\n"
                f"- `{self.config.DISCORD['PREFIX']}monitor add|remove|list account|token|collection [value]` - Manage monitored items\n"
                f"- `{self.config.DISCORD['PREFIX']}bot_help` - Show this help message\n"
                f"- `{self.config.DISCORD['PREFIX']}stats` - View current blockchain statistics\n"
                f"- `{self.config.DISCORD['PREFIX']}recent` - See recent significant events\n"
                f"- `{self.config.DISCORD['PREFIX']}campaign` - See active community campaigns\n"
                f"- `{self.config.DISCORD['PREFIX']}status` - Check the bot status\n"
                f"- `{self.config.DISCORD['PREFIX']}latest` - Get the latest blockchain events\n\n"
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
        
        @self.bot.command(name='status')
        async def status(ctx):
            """Check the bot status."""
            uptime = datetime.now() - datetime.now()  # Replace with actual uptime calculation
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            status_msg = (
                f"**Bot Status**: Online\n"
                f"**Uptime**: {hours}h {minutes}m {seconds}s\n"
                f"**Events Processed**: {len(self.posted_events)}\n"
                f"**Queue Size**: {self.message_queue.qsize()}"
            )
            await ctx.send(status_msg)
        
        @self.bot.command(name='latest')
        async def latest(ctx):
            """Get the latest blockchain events."""
            if not self.blockchain_monitor:
                await ctx.send("Blockchain monitor not available")
                return
                
            recent_events = getattr(self.blockchain_monitor, 'recent_events', [])
            if not recent_events:
                await ctx.send("No significant events detected recently")
                return
                
            response = ["**Latest Blockchain Events**:"]
            for event in recent_events[-5:]:
                event_type = event.get("event_category", "unknown")
                description = event.get("description", "No description available")
                response.append(f"- {event_type}: {description}")
                
            await ctx.send("\n".join(response))
        
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
                question = question.replace(f'<@{self.bot.user.id}>', '').strip()
            
            # Get answer
            response = self.ai_module.get_answer(question)
            
            # Only respond if confidence is high enough
            if response["confidence"] >= 0.5:
                await message.reply(response["answer"])
    
    def post_blockchain_event(self, event):
        """Queue a blockchain event for posting to Discord.
        
        Args:
            event (dict): Enriched blockchain event data
        """
        # Generate insights using AI module
        insights = self.ai_module.generate_insights(event)
        
        # Create a unique identifier for this event to avoid duplicates
        event_id = f"{event.get('version', '')}-{event.get('event_handle', '')}-{event.get('field_name', '')}"
        
        # Check if we've already posted this event
        if event_id in self.posted_events:
            logger.info(f"Skipping already posted event: {event_id}")
            return
            
        # Add to posted events set
        self.posted_events.add(event_id)
        
        # Limit the size of posted_events to prevent memory issues
        if len(self.posted_events) > 1000:
            # Remove oldest entries
            self.posted_events = set(list(self.posted_events)[-500:])
            
        # Create Discord embed with a more conversational style
        embed = discord.Embed(
            title=insights["title"],
            description=insights["message"],
            color=self._get_color_for_event_type(event.get("event_category", "other")),
            timestamp=datetime.now()
        )
        
        # Add a random conversation starter or question based on event type
        conversation_starters = {
            "nft_mint": [
                "What do you think of this new NFT? 🤔",
                "Anyone planning to collect from this series? 🖼️",
                "This artwork caught my eye! What about you? 👀"
            ],
            "nft_transfer": [
                "Interesting NFT movement! Any thoughts on why? 🧐",
                "NFT trading is heating up! Anyone else noticing this trend? 📈",
                "This collection seems to be getting attention! Are you following it? 👀"
            ],
            "coin_transfer": [
                "That's some APT on the move! Market signal or just regular activity? 💰",
                "What do you make of this transaction? Important or routine? 🤔",
                "Anyone else watching these fund movements? What's your take? 💭"
            ],
            "collection_creation": [
                "New collection alert! Anyone planning to check it out? 🚀",
                "Fresh creative work on Aptos! What kind of collections excite you? 🎨",
                "New collections are always exciting! What are you looking forward to? ✨"
            ],
            "other": [
                "What's everyone's take on this? 💬",
                "Interesting blockchain activity! Thoughts? 🤔",
                "Anyone following this kind of activity on Aptos? 👀"
            ]
        }
        
        # Select a random conversation starter based on event type
        event_category = event.get("event_category", "other")
        starters = conversation_starters.get(event_category, conversation_starters["other"])
        conversation_starter = random.choice(starters)
        
        # Add fields with additional information
        embed.add_field(name="Account", value=event.get("account", "Unknown"), inline=True)
        
        # Add token information if available
        if "token_name" in event:
            embed.add_field(name="Token", value=event["token_name"], inline=True)
            embed.add_field(name="Collection", value=event.get("collection_name", "Unknown"), inline=True)
            
        # Add amount for coin transfers
        if "amount_apt" in event:
            embed.add_field(name="Amount", value=f"{event['amount_apt']:.8f} APT", inline=True)
            
        # Add transaction link if available
        if "transaction_url" in event and event["transaction_url"]:
            embed.add_field(name="Transaction", value=f"[View on Explorer]({event['transaction_url']})", inline=False)
            
        # Add the conversation starter as a field
        embed.add_field(name="💬 Let's chat!", value=conversation_starter, inline=False)
            
        # Add footer with analysis
        if "analysis" in insights:
            embed.set_footer(text=insights["analysis"])
            
        # Queue the message for posting
        asyncio.run_coroutine_threadsafe(self.message_queue.put(embed), self.bot.loop)
        logger.info(f"Queued blockchain event for posting: {event.get('event_category', 'unknown')}")
    
    def _get_color_for_event_type(self, event_type):
        """Get Discord embed color based on event type."""
        colors = {
            "nft_mint": 0x00FF00,  # Green
            "nft_transfer": 0x0099FF,  # Blue
            "coin_transfer": 0xFFAA00,  # Orange
            "collection_creation": 0xFF00FF,  # Purple
            "other": 0x777777  # Gray
        }
        return colors.get(event_type, 0x777777)
    
    def _format_address(self, address):
        """Format an address for display by shortening it."""
        if not address or len(address) < 10:
            return address
            
        return f"{address[:6]}...{address[-4:]}"
    
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
                await channel.send(embed=message_data)
                logger.info(f"Posted message to Discord: {message_data.title[:30]}...")
                
                # Mark task as done
                self.message_queue.task_done()
                
                # Add delay for rate limiting
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error processing message queue: {str(e)}")
    
    def run(self):
        """Run the Discord bot."""
        logger.info("Starting Discord bot")
        self.bot.run(self.config.DISCORD["BOT_TOKEN"])
