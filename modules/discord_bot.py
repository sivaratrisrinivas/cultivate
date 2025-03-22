# modules/discord_bot.py
import discord
import os
import asyncio
import aiohttp
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
        
        self.bot = commands.Bot(command_prefix=config.DISCORD["PREFIX"], intents=intents, help_command=None)
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
            
            # Start message queue processor
            self.process_message_queue.start()
        
        @self.bot.event
        async def on_message(message):
            """Handle incoming messages."""
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return
                
            # Process commands first
            await self.bot.process_commands(message)
            
            # Then handle regular messages
            await self._handle_message(message)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            """Handle command errors."""
            if isinstance(error, commands.CommandNotFound):
                logger.warning(f"Command not found: {ctx.message.content}")
                return
                
            if isinstance(error, commands.MissingRequiredArgument):
                logger.warning(f"Missing required argument: {error}")
                await ctx.send(f"Missing required argument: {error.param.name}. Use `!help` for command usage.")
                return
                
            if isinstance(error, commands.BadArgument):
                logger.warning(f"Bad argument: {error}")
                await ctx.send(f"Invalid argument: {error}. Use `!help` for command usage.")
                return
                
            # Log other errors
            logger.error(f"Command error: {error}")
            await ctx.send("An error occurred while processing your command. Please try again later.")
        
        @self.bot.command(name='events')
        async def events_command(ctx, count: int = 5):
            """Show recent blockchain events.
            
            Args:
                count: Number of events to show (default: 5)
            """
            if not self.blockchain_monitor:
                await ctx.send("Blockchain monitor not available")
                return
                
            # Limit count to a reasonable number
            count = min(max(count, 1), 10)
            
            # Get recent events
            recent_events = getattr(self.blockchain_monitor, 'recent_events', [])
            
            if not recent_events:
                await ctx.send("No recent events available")
                return
                
            # Get the most recent events
            events_to_show = recent_events[-count:]
            
            # Create an embed for each event
            for event in events_to_show:
                event_category = event.get('event_category', 'unknown')
                
                # Generate insights using AI module
                insights = self.ai_module.generate_insights(event)
                
                # Create Discord embed
                embed = discord.Embed(
                    title=insights["title"],
                    description=insights["message"],
                    color=self._get_color_for_event_type(event_category),
                    timestamp=datetime.now()
                )
                
                # Add fields with additional information
                embed.add_field(name="Account", value=self._format_account_link(event.get("account", "Unknown"), event.get("account_url", "")), inline=True)
                
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
                
                await ctx.send(embed=embed)
        
        @self.bot.command(name='status')
        async def status_command(ctx):
            """Show blockchain monitor status."""
            if not self.blockchain_monitor:
                await ctx.send("Blockchain monitor not available")
                return
                
            # Get status information
            events_processed = getattr(self.blockchain_monitor, 'events_processed_count', 0)
            significant_events = getattr(self.blockchain_monitor, 'significant_events_count', 0)
            monitored_accounts = len(getattr(self.blockchain_monitor, 'validated_accounts', []))
            event_handles = len(getattr(self.blockchain_monitor, 'event_handles', []))
            last_version = getattr(self.blockchain_monitor, 'last_processed_version', 0)
            
            # Create status embed
            embed = discord.Embed(
                title="Blockchain Monitor Status",
                description="Current status of the blockchain monitor",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Events Processed", value=str(events_processed), inline=True)
            embed.add_field(name="Significant Events", value=str(significant_events), inline=True)
            embed.add_field(name="Monitored Accounts", value=str(monitored_accounts), inline=True)
            embed.add_field(name="Event Handles", value=str(event_handles), inline=True)
            embed.add_field(name="Last Processed Version", value=str(last_version), inline=True)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='metrics')
        async def metrics_command(ctx):
            """Show blockchain metrics."""
            if not self.blockchain_monitor:
                await ctx.send("Blockchain monitor not available")
                return
                
            # Get metrics information
            event_types = getattr(self.blockchain_monitor, 'event_type_counts', {})
            
            # Create metrics embed
            embed = discord.Embed(
                title="Blockchain Metrics",
                description="Current blockchain metrics",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            # Add event type distribution
            event_types_str = "\n".join([f"{k}: {v}" for k, v in event_types.items()])
            if event_types_str:
                embed.add_field(name="Event Types", value=event_types_str, inline=False)
            else:
                embed.add_field(name="Event Types", value="No events recorded yet", inline=False)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='custom_help')
        async def custom_help_command(ctx):
            """Show help information."""
            try:
                logger.info(f"Custom help command invoked by {ctx.author}")
                embed = discord.Embed(
                    title="Cultivate - Aptos Blockchain Monitor",
                    description="Welcome to Cultivate! This bot tracks and reports on Aptos blockchain events in real-time with AI-powered insights.",
                    color=discord.Color.from_rgb(127, 90, 240),  # Using the primary color
                    timestamp=datetime.now()
                )
                
                # Add command information
                embed.add_field(
                    name="!events [count]", 
                    value="Shows recent blockchain events. You can specify how many events to show (default: 5, max: 10).\n"
                          "Example: `!events 3` shows the 3 most recent events.", 
                    inline=False
                )
                
                embed.add_field(
                    name="!status", 
                    value="Shows the current status of the blockchain monitor, including events processed, significant events, and monitored accounts.", 
                    inline=False
                )
                
                embed.add_field(
                    name="!metrics", 
                    value="Shows blockchain metrics, including event type distribution and other statistics.", 
                    inline=False
                )
                
                embed.add_field(
                    name="!custom_help", 
                    value="Shows this help message with command information.", 
                    inline=False
                )
                
                # Add usage instructions
                embed.add_field(
                    name="How to Use This Bot",
                    value="1. Use this bot in the designated channel\n"
                          "2. Type any of the commands listed above\n"
                          "3. The bot will respond with real-time data from the Aptos blockchain\n"
                          "4. You can interact with the data by clicking on account or transaction links",
                    inline=False
                )
                
                # Add footer with additional info
                embed.set_footer(text="All data is fetched in real-time from the Aptos blockchain")
                
                await ctx.send(embed=embed)
                logger.info("Custom help command executed successfully")
            except Exception as e:
                logger.error(f"Error executing custom_help command: {str(e)}")
                await ctx.send("Sorry, there was an error displaying the help information. Please try again later.")
        
        @self.bot.command(name='help')
        async def help_command(ctx):
            """Redirect to custom help command."""
            try:
                logger.info(f"Help command invoked by {ctx.author}, redirecting to custom_help")
                await custom_help_command(ctx)
            except Exception as e:
                logger.error(f"Error redirecting to custom_help command: {str(e)}")
                await ctx.send("Sorry, there was an error displaying the help information. Please try again later.")
        
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
        
    async def _handle_message(self, message):
        """Handle a regular message.
        
        Args:
            message: Discord message object
        """
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
    
    async def send_webhook(self, embed, webhook_url):
        """Send a message to a Discord webhook.
        
        Args:
            embed: The Discord embed to send
            webhook_url: The webhook URL to send to
        """
        try:
            # Create a Discord webhook
            webhook = discord.Webhook.from_url(webhook_url, session=None)
            
            # Use an async context manager for the session
            async with aiohttp.ClientSession() as session:
                webhook_with_session = discord.Webhook.from_url(webhook_url, session=session)
                await webhook_with_session.send(embed=embed)
                
            logger.info("Webhook message sent successfully")
            return True
        except Exception as e:
            logger.error(f"Error sending webhook: {str(e)}")
            return False
    
    def post_blockchain_event(self, event):
        """Post a blockchain event to the designated Discord channel.
        
        Args:
            event: The blockchain event to post
        
        Returns:
            bool: True if the event was successfully queued, False otherwise
        """
        try:
            # Generate a unique event ID based on its content
            event_id = None
            if 'version' in event and 'sequence_number' in event:
                event_id = f"{event['version']}_{event['sequence_number']}"
            elif 'transaction_version' in event:
                event_id = f"{event['transaction_version']}"
            else:
                # Create a hash of the event data for non-standard events
                import hashlib
                event_str = str(sorted(event.items()))
                event_id = hashlib.md5(event_str.encode()).hexdigest()
            
            # Check if we've already posted this event
            if event_id in self.posted_events:
                logger.info(f"Skipping duplicate event with ID: {event_id}")
                return False
            
            # Add to posted events set
            self.posted_events.add(event_id)
            
            # Limit the size of posted_events to avoid memory issues
            if len(self.posted_events) > 1000:
                # Keep only the most recent 500 events
                self.posted_events = set(list(self.posted_events)[-500:])
            
            # Process event data
            event_category = event.get('event_category', 'unknown')
            logger.info(f"Processing blockchain event for Discord: {event_category}")
            
            # Generate insights using AI module
            insights = self.ai_module.generate_insights(event)
            
            # Create Discord embed
            embed = discord.Embed(
                title=insights["title"],
                description=insights["message"],
                color=self._get_color_for_event_type(event_category),
                timestamp=datetime.now()
            )
            
            # Generate meme image if enabled in config
            if self.config.AI.get("GENERATE_IMAGES", False):
                try:
                    # Use the AI module to generate a meme
                    meme_data = self.ai_module.generate_meme_for_event(event)
                    
                    # Add meme image to embed if available
                    if meme_data and 'image_url' in meme_data:
                        embed.set_image(url=meme_data['image_url'])
                        logger.info(f"Added meme image to Discord message: {meme_data['image_url'][:50]}...")
                except Exception as meme_error:
                    logger.error(f"Error generating meme: {str(meme_error)}")
            
            # Add fields with additional information
            embed.add_field(name="Account", value=self._format_account_link(event.get("account", "Unknown"), event.get("account_url", "")), inline=True)
            
            # Add token information if available
            if "token_name" in event:
                embed.add_field(name="Token", value=event["token_name"], inline=True)
                
            # Add collection if available
            if "collection_name" in event:
                embed.add_field(name="Collection", value=event["collection_name"], inline=True)
                
            # Add amount for coin transfers
            if "amount_apt" in event:
                embed.add_field(name="Amount", value=f"{event['amount_apt']:.8f} APT", inline=True)
                
            # Add transaction link if available
            if "transaction_url" in event and event["transaction_url"]:
                embed.add_field(name="Transaction", value=f"[View on Explorer]({event['transaction_url']})", inline=False)
            
            # Add conversation starter
            embed.add_field(name="Let's chat!", value="What do you think about this event?", inline=False)
            
            # Store the message data instead of directly adding to the queue
            # This avoids the async loop error when called from non-async contexts
            message_data = {'embed': embed, 'event_id': event_id}
            
            # Always use the sync approach to avoid async context issues
            self._sync_add_to_queue(message_data)
            logger.info(f"Added event {event_id} to message queue (sync)")
            
            return True
        except Exception as e:
            logger.error(f"Error posting blockchain event: {str(e)}")
            return False
    
    def _sync_add_to_queue(self, message_data):
        """Add a message to the queue from a non-async context.
        
        Args:
            message_data: The message data to add to the queue
        """
        # Store in a class level list that will be processed by the queue processor
        if not hasattr(self, '_pending_messages'):
            self._pending_messages = []
        self._pending_messages.append(message_data)
    
    def _format_account_link(self, account, account_url):
        """Format an account link for Discord embed.
        
        Args:
            account (str): Account address
            account_url (str): URL to the account on explorer
            
        Returns:
            str: Formatted account link
        """
        if not account:
            return "Unknown Account"
            
        # Format the account address to be shorter
        short_account = account[:8] + '...' + account[-4:] if len(account) > 12 else account
        
        # Check if the account URL is valid
        if account_url and account_url.startswith('http'):
            # Add a note about potential "account not found" message
            return f"[{short_account}]({account_url})\n(Note: New accounts may show as 'not found' on explorer)"
        else:
            return short_account
    
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
        """Process messages in the queue with rate limiting."""
        # First, check if there are any pending messages from non-async contexts
        if hasattr(self, '_pending_messages') and self._pending_messages:
            # Get the count before moving
            pending_count = len(self._pending_messages)
            
            # Move pending messages to the async queue
            for message in self._pending_messages:
                await self.message_queue.put(message)
            
            # Clear the pending messages
            self._pending_messages = []
            logger.info(f"Moved {pending_count} pending messages to async queue")
        
        # Check if there are any messages to process
        if self.message_queue.empty():
            return
        
        # Check if we should post a batch now (15-minute interval)
        current_time = datetime.now()
        time_since_last_post = (current_time - self.last_post_time).total_seconds() / 60
        
        if time_since_last_post < 15:
            # Not time to post yet
            return
        
        # Time to post! Process events in the queue
        try:
            # Get up to 5 messages to post as a batch
            messages_to_post = []
            count = 0
            
            while not self.message_queue.empty() and count < 5:
                message = await self.message_queue.get()
                messages_to_post.append(message)
                self.message_queue.task_done()
                count += 1
            
            if messages_to_post:
                # Get channel
                webhook_url = self.config.DISCORD.get("WEBHOOK_URL", None)
                channel_id = self.config.DISCORD.get("CHANNEL_ID", None)
                
                if webhook_url:
                    # Post each message
                    for message in messages_to_post:
                        # Post with webhook
                        await self.send_webhook(message['embed'], webhook_url)
                        # Brief delay between messages
                        await asyncio.sleep(1)
                elif channel_id:
                    # Get channel
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        # Post each message
                        for message in messages_to_post:
                            await channel.send(embed=message['embed'])
                            # Brief delay between messages
                            await asyncio.sleep(1)
                
                # Update last post time
                self.last_post_time = current_time
                logger.info(f"Posted batch of {len(messages_to_post)} blockchain events to Discord")
        except Exception as e:
            logger.error(f"Error processing message queue: {str(e)}")
    
    def run(self):
        """Run the Discord bot."""
        logger.info("Starting Discord bot")
        try:
            # Check if token is available
            if not self.config.DISCORD["BOT_TOKEN"]:
                logger.error("Discord bot token is missing. Please check your .env file.")
                logger.info("Application will continue running without Discord bot functionality")
                return
                
            # Log token length for debugging (don't log the actual token)
            token_length = len(self.config.DISCORD["BOT_TOKEN"]) if self.config.DISCORD["BOT_TOKEN"] else 0
            logger.info(f"Discord bot token length: {token_length} characters")
            
            # Check if channel ID is valid
            if not self.channel_id or self.channel_id == 0:
                logger.error("Discord channel ID is missing or invalid. Please check your .env file.")
                logger.info("Application will continue running without Discord bot functionality")
                return
                
            logger.info(f"Discord bot will post to channel ID: {self.channel_id}")
            
            # Run the bot
            self.bot.run(self.config.DISCORD["BOT_TOKEN"])
        except discord.errors.LoginFailure as e:
            logger.error(f"Discord login failed: {str(e)}")
            logger.error("Discord bot token appears to be invalid. Please check your DISCORD_BOT_TOKEN in the .env file.")
            logger.info("Application will continue running without Discord bot functionality")
        except Exception as e:
            logger.error(f"Error starting Discord bot: {str(e)}")
            # If the token is invalid, log a more helpful message
            if "improper token" in str(e).lower() or "401: unauthorized" in str(e).lower():
                logger.error("Discord bot token appears to be invalid. Please check your DISCORD_BOT_TOKEN in the .env file.")
            # Continue running the application without the Discord bot
            logger.info("Application will continue running without Discord bot functionality")
    
    def _generate_fallback_title(self, event):
        """Generate a fallback title for an event.
        
        Args:
            event (dict): Blockchain event data
            
        Returns:
            str: Fallback title for the event
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
    
    def _generate_fallback_message(self, event):
        """Generate a fallback message for an event.
        
        Args:
            event (dict): Blockchain event data
            
        Returns:
            str: Fallback message for the event
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

    def test_discord_connection(self):
        """Test the Discord connection by sending a test message.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Testing Discord connection...")
        
        # Create a test embed
        embed = discord.Embed(
            title="🧪 Discord Connection Test",
            description="This is a test message to verify the Discord connection is working.",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Application", value="Cultivate Blockchain Monitor", inline=True)
        embed.add_field(name="Status", value="Online", inline=True)
        embed.add_field(name="Time", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_footer(text="If you can see this message, Discord notifications are working!")
        
        # Try webhook first
        webhook_sent = False
        webhook_url = self.config.DISCORD_NOTIFICATIONS.get("WEBHOOK_URL")
        if webhook_url:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                webhook_sent = loop.run_until_complete(self.send_webhook(embed, webhook_url))
                loop.close()
                logger.info(f"Test webhook sent: {webhook_sent}")
            except Exception as e:
                logger.error(f"Error sending test webhook: {str(e)}")
        
        # Try direct channel posting
        channel_sent = False
        try:
            # Create a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create a temporary function to send the message directly
            async def send_direct():
                try:
                    # Create a temporary client
                    client = discord.Client(intents=discord.Intents.default())
                    
                    # Define on_ready event
                    @client.event
                    async def on_ready():
                        try:
                            # Get the channel
                            channel = client.get_channel(int(self.channel_id))
                            if channel:
                                await channel.send(embed=embed)
                                logger.info(f"Sent test message directly to channel {self.channel_id}")
                                await client.close()
                                return True
                            else:
                                logger.error(f"Channel with ID {self.channel_id} not found")
                                await client.close()
                                return False
                        except Exception as e:
                            logger.error(f"Error sending direct test message: {str(e)}")
                            await client.close()
                            return False
                    
                    # Run the client
                    await client.start(self.config.DISCORD["BOT_TOKEN"])
                    return True
                except Exception as e:
                    logger.error(f"Error in send_direct: {str(e)}")
                    return False
            
            # Try to send directly
            channel_sent = loop.run_until_complete(send_direct())
            loop.close()
        except Exception as e:
            logger.error(f"Error creating new event loop for direct test message: {str(e)}")
        
        # Return result
        return webhook_sent or channel_sent

    async def test_webhook_directly(self):
        """Test the webhook directly without using the Discord bot.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Testing webhook directly...")
        
        webhook_url = self.config.DISCORD_NOTIFICATIONS.get("WEBHOOK_URL")
        if not webhook_url:
            logger.error("No webhook URL configured")
            return False
            
        try:
            import aiohttp
            import json
            
            # Create a simple webhook payload
            webhook_data = {
                "content": "🧪 **WEBHOOK TEST** - If you can see this message, webhook notifications are working!",
                "username": "Aptos Blockchain Monitor",
                "embeds": [
                    {
                        "title": "Webhook Test",
                        "description": "This is a test message sent directly via webhook.",
                        "color": 65280,  # Green
                        "fields": [
                            {
                                "name": "Application",
                                "value": "Cultivate Blockchain Monitor",
                                "inline": True
                            },
                            {
                                "name": "Status",
                                "value": "Online",
                                "inline": True
                            },
                            {
                                "name": "Time",
                                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "inline": True
                            }
                        ],
                        "footer": {
                            "text": "If you can see this message, webhook notifications are working!"
                        }
                    }
                ]
            }
            
            logger.info(f"Sending test webhook to {webhook_url[:20]}...")
            logger.info(f"Webhook payload: {json.dumps(webhook_data)[:200]}...")
            
            # Send webhook using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=webhook_data) as response:
                    status = response.status
                    logger.info(f"Webhook response status: {status}")
                    
                    if status == 204:
                        logger.info("Successfully sent test webhook")
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"Failed to send test webhook: HTTP {status}, Response: {response_text}")
                        return False
        except Exception as webhook_error:
            logger.error(f"Error sending test webhook: {str(webhook_error)}")
            return False
