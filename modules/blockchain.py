import json
import logging
import time
import threading
import hashlib
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

# Import the Aptos SDK
from aptos_sdk.async_client import RestClient
from aptos_sdk.account import Account
from aptos_sdk.transactions import EntryFunction, TransactionArgument, TransactionPayload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add file handler for more detailed logging
file_handler = logging.FileHandler('logs/modules.blockchain-2025-03-15-new.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class BlockchainMonitor:
    """Class to monitor blockchain events and trigger callbacks."""
    
    def __init__(self, config, node_url: str = "https://fullnode.mainnet.aptoslabs.com/v1"):
        """Initialize the blockchain monitor.
        
        Args:
            config: Configuration object
            node_url: URL of the Aptos node to connect to
        """
        self.config = config
        self.node_url = node_url
        self.client = RestClient(node_url)
        self.running = False
        self.event_callbacks = []
        self.accounts_of_interest = [
            "0x1",  # Core framework
            "0x0108bc32f7de18a5f6e1e7d6ee7aff9f5fc858d0d87ac0da94dd8d2a5d267d6b",  # Topaz marketplace
            "0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92",  # BlueMove marketplace
            "0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4",  # Souffl3 marketplace
            "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2",  # Pontem DEX
            "0x25a125ffc4634e095d9fbd8ec34e0b1cef2c8cd1b66f347bef9f4182b883796c",  # Econia DEX
        ]
        self.validated_accounts = []
        self.event_handles = []
        self.recent_events = []
        self.last_processed_version = self._get_last_processed_version()
        self.start_time = time.time()
        self.polling_interval = config.BLOCKCHAIN["POLLING_INTERVAL"]
        
        # Initialize metrics counters
        self.events_processed_count = 0
        self.significant_events_count = 0
        
        # Initialize activity tracking
        self.event_type_counts = {}
        self.account_activity = {}
        self.token_activity = {}
        self.collection_activity = {}
        
        # Initialize time-based metrics
        self.hourly_event_counts = [0] * 24
        self.daily_event_counts = [0] * 7
        
        self.explorer_url = "https://explorer.aptoslabs.com"
        
        # Monitored accounts, tokens, and collections
        self.monitored_accounts = []
        self.monitored_tokens = []
        self.monitored_collections = []
        
        # Enhanced metrics tracking
        self.hourly_event_counts = [0] * 24  # Events per hour for the last 24 hours
        self.daily_event_counts = [0] * 7    # Events per day for the last 7 days
        self.last_metrics_update = time.time()
        self.version_history = []    # Track blockchain version over time
        
        # Add default monitored items from config if available
        if hasattr(self.config, 'MONITOR') and self.config.MONITOR:
            if 'ACCOUNTS' in self.config.MONITOR and self.config.MONITOR['ACCOUNTS']:
                self.monitored_accounts.extend(self.config.MONITOR['ACCOUNTS'])
            if 'TOKENS' in self.config.MONITOR and self.config.MONITOR['TOKENS']:
                self.monitored_tokens.extend(self.config.MONITOR['TOKENS'])
            if 'COLLECTIONS' in self.config.MONITOR and self.config.MONITOR['COLLECTIONS']:
                self.monitored_collections.extend(self.config.MONITOR['COLLECTIONS'])
            
    def _get_last_processed_version(self):
        """Get the last processed version from storage."""
        try:
            with open("last_version.txt", "r") as f:
                return int(f.read().strip())
        except:
            # Start from a recent but not too recent version to get some events
            # Use a lower value to ensure we process some events
            return 2481600000  # Set to a lower value to get some events
            
    def _save_last_processed_version(self, version):
        """Save the last processed version to storage."""
        with open("last_version.txt", "w") as f:
            f.write(str(version))
    
    def register_event_callback(self, callback: Callable):
        """Register a callback function to be called when an event is detected.
        
        Args:
            callback: Function to call when an event is detected
        """
        logger.info(f"Registered event callback: {callback.__name__}")
        self.event_callbacks.append(callback)
    
    async def validate_accounts(self):
        """Validate that the accounts of interest exist on the blockchain."""
        valid_accounts = []
        
        for account in self.accounts_of_interest:
            try:
                # Use direct REST API call instead of SDK
                response = requests.get(f"{self.node_url}/accounts/{account}")
                if response.status_code == 200:
                    logger.info(f"Account validated: {account}")
                    valid_accounts.append(account)
                else:
                    logger.warning(f"Account not found: {account}")
            except Exception as e:
                logger.warning(f"Account {account} not found: {str(e)}")
                
        self.validated_accounts = valid_accounts
        return valid_accounts
    
    async def discover_event_handles(self):
        """Discover event handles for the validated accounts."""
        event_handles = []
        
        # Define common event handles to look for
        common_handles = [
            {"handle": "0x1::coin::CoinStore", "field": "deposit_events"},
            {"handle": "0x1::coin::CoinStore", "field": "withdraw_events"},
            {"handle": "0x3::token::TokenStore", "field": "deposit_events"},
            {"handle": "0x3::token::TokenStore", "field": "withdraw_events"},
            {"handle": "0x3::token::Collections", "field": "create_collection_events"},
            {"handle": "0x3::token::Collections", "field": "create_token_data_events"},
            {"handle": "0x3::token::Collections", "field": "mint_token_events"},
        ]
        
        # For each validated account, check if it has any of the common event handles
        for account in self.validated_accounts:
            for handle_info in common_handles:
                try:
                    # Use direct REST API call instead of SDK
                    resource_type = handle_info["handle"]
                    field_name = handle_info["field"]
                    
                    # Get the resource that contains the event handle
                    try:
                        response = requests.get(f"{self.node_url}/accounts/{account}/resource/{resource_type}")
                        if response.status_code == 200:
                            resource = response.json()
                            
                            # Check if the field exists in the resource
                            if "data" in resource and field_name in resource["data"]:
                                handle = {
                                    "account": account,
                                    "event_handle": resource_type,
                                    "field_name": field_name
                                }
                                event_handles.append(handle)
                                logger.info(f"Discovered event handle: {account}/{resource_type}/{field_name}")
                    except Exception as e:
                        # Resource doesn't exist or field doesn't exist
                        pass
                        
                except Exception as e:
                    # This handle doesn't exist for this account, which is expected for many accounts
                    pass
        
        self.event_handles = event_handles
        return event_handles
    
    async def fetch_events(self):
        """Fetch events from the blockchain using direct REST API calls."""
        all_events = []
        current_version = await self.get_latest_version()
        
        if current_version <= self.last_processed_version:
            logger.info(f"No new blocks since last check (current: {current_version}, last: {self.last_processed_version})")
            return []
        
        logger.info(f"Fetching events from version {self.last_processed_version} to {current_version}")
        
        # Fetch events for each discovered event handle
        for handle in self.event_handles:
            try:
                # Use async REST API call
                url = f"{self.node_url}/accounts/{handle['account']}/events/{handle['event_handle']}/{handle['field_name']}"
                logger.debug(f"Fetching events from URL: {url}")
                
                # Use a single approach for fetching data to avoid event loop issues
                try:
                    response = await self.client.client.get(url)
                    events_data = response.json()
                except Exception as e:
                    # If any error occurs, use a simple synchronous request as fallback
                    logger.warning(f"Error with async request, using synchronous fallback: {str(e)}")
                    import requests
                    response = requests.get(url)
                    if response.status_code == 200:
                        events_data = response.json()
                    else:
                        logger.error(f"Error fetching events: {response.status_code} - {response.text}")
                        events_data = []
                
                if events_data:
                    logger.info(f"Found {len(events_data)} events for {handle['account']}/{handle['event_handle']}/{handle['field_name']}")
                    
                    # Filter events by version if needed
                    filtered_events = []
                    for event in events_data:
                        event_version = int(event.get("version", 0))
                        
                        if event_version > self.last_processed_version:
                            # Enrich event with handle information
                            event["account"] = handle["account"]
                            event["event_handle"] = handle["event_handle"]
                            event["field_name"] = handle["field_name"]
                            
                            # Add event type based on handle
                            if "token::TokenStore/deposit_events" in f"{handle['event_handle']}/{handle['field_name']}":
                                event["type"] = "token_deposit"
                            elif "token::TokenStore/withdraw_events" in f"{handle['event_handle']}/{handle['field_name']}":
                                event["type"] = "token_withdrawal"
                            elif "coin::CoinStore/deposit_events" in f"{handle['event_handle']}/{handle['field_name']}":
                                event["type"] = "coin_deposit"
                            elif "coin::CoinStore/withdraw_events" in f"{handle['event_handle']}/{handle['field_name']}":
                                event["type"] = "coin_withdrawal"
                            else:
                                event["type"] = "other"
                            
                            filtered_events.append(event)
                    
                    if filtered_events:
                        logger.info(f"Found {len(filtered_events)} new events after filtering for {handle['account']}/{handle['event_handle']}/{handle['field_name']}")
                        all_events.extend(filtered_events)
                    else:
                        logger.info(f"No new events after filtering for {handle['account']}/{handle['event_handle']}/{handle['field_name']}")
            except Exception as e:
                logger.error(f"Error fetching events for {handle['account']}/{handle['event_handle']}/{handle['field_name']}: {str(e)}")
        
        # Update last processed version
        if all_events and current_version > self.last_processed_version:
            self.last_processed_version = current_version
            
        if not all_events:
            logger.info("No new events detected")
            
        return all_events
    
    async def get_latest_version(self):
        """Get the latest version (block height) of the blockchain."""
        try:
            # Try to use the async client first
            try:
                response = await self.client.client.get(f"{self.node_url}")
                ledger_info = response.json()
                return int(ledger_info.get("ledger_version", 0))
            except RuntimeError as e:
                # If we get an event loop error, fall back to synchronous approach
                if "Event loop is closed" in str(e):
                    logger.warning("Event loop is closed, falling back to synchronous request")
                    import requests
                    response = requests.get(f"{self.node_url}")
                    if response.status_code == 200:
                        ledger_info = response.json()
                        return int(ledger_info.get("ledger_version", 0))
                else:
                    # Re-raise if it's not an event loop error
                    raise
            return 0
        except Exception as e:
            logger.error(f"Error getting latest version: {str(e)}")
            return 0
    
    def process_events(self, events, discord_bot=None):
        """Process blockchain events and trigger registered callbacks.
        
        Args:
            events: List of blockchain events
            discord_bot: Optional Discord bot instance for notifications
        
        Returns:
            List of processed significant events
        """
        significant_events = []
        processed_event_ids = set()
        
        try:
            for event in events:
                try:
                    # Generate a unique ID for this event
                    event_id = None
                    if 'version' in event and 'sequence_number' in event:
                        event_id = f"{event['version']}_{event['sequence_number']}"
                    elif 'transaction_version' in event:
                        event_id = f"{event['transaction_version']}"
                    else:
                        # Use any unique identifiers available
                        import hashlib
                        event_str = str(sorted(event.items()))
                        event_id = hashlib.md5(event_str.encode()).hexdigest()
                    
                    # Skip if we've already processed this event
                    if event_id in processed_event_ids:
                        logger.debug(f"Skipping duplicate event with ID: {event_id}")
                        continue
                    
                    # Add to processed events
                    processed_event_ids.add(event_id)
                    
                    # Update last processed version if higher than current one
                    event_version = int(event.get('version', 0))
                    if event_version > self.last_processed_version:
                        self.last_processed_version = event_version
                        self._save_last_processed_version(event_version)
                    
                    # Check if the event is significant
                    if self._is_significant_event(event):
                        logger.info(f"Significant event found: {event.get('type', 'unknown')}")
                        
                        # Enrich the event with additional information
                        enriched_event = self._enrich_event(event)
                        
                        # Update metrics for this event
                        self._update_metrics(enriched_event)
                        
                        # Add to list of significant events
                        significant_events.append(enriched_event)
                        
                        # Add to recent events list, keeping only the most recent 100
                        self.recent_events.append(enriched_event)
                        if len(self.recent_events) > 100:
                            self.recent_events = self.recent_events[-100:]
                        
                        # Trigger Discord notification if a Discord bot is provided
                        if discord_bot:
                            logger.info(f"Sending event to Discord bot: {enriched_event.get('event_category', 'unknown')}")
                            discord_bot.post_blockchain_event(enriched_event)
                        
                        # Trigger registered callbacks
                        for callback in self.event_callbacks:
                            try:
                                callback(enriched_event)
                            except Exception as callback_error:
                                logger.error(f"Error in callback {callback.__name__}: {str(callback_error)}")
                                
                except Exception as event_error:
                    logger.error(f"Error processing individual event: {str(event_error)}")
                    continue
                    
            # Update significant events count
            self.significant_events_count += len(significant_events)
            
            return significant_events
        except Exception as e:
            logger.error(f"Error processing events: {str(e)}")
            return []
    
    def _update_metrics(self, event):
        """Update metrics based on an event.
        
        Args:
            event: The event to update metrics for
        """
        try:
            # Update event type counts
            event_category = event.get('event_category', 'other')
            self.event_type_counts[event_category] = self.event_type_counts.get(event_category, 0) + 1
            
            # Update account activity
            if 'account' in event:
                account = event.get('account')
                if account not in self.account_activity:
                    self.account_activity[account] = {
                        'total_events': 0,
                        'first_seen': datetime.now().isoformat(),
                        'last_seen': datetime.now().isoformat(),
                        'event_types': {}
                    }
                
                self.account_activity[account]['total_events'] += 1
                self.account_activity[account]['last_seen'] = datetime.now().isoformat()
                
                # Track event types for this account
                self.account_activity[account]['event_types'][event_category] = \
                    self.account_activity[account]['event_types'].get(event_category, 0) + 1
            
            # Update token activity
            if 'token_name' in event:
                token = event.get('token_name')
                if token not in self.token_activity:
                    self.token_activity[token] = {
                        'total_events': 0,
                        'first_seen': datetime.now().isoformat(),
                        'last_seen': datetime.now().isoformat(),
                        'event_types': {}
                    }
                
                self.token_activity[token]['total_events'] += 1
                self.token_activity[token]['last_seen'] = datetime.now().isoformat()
                
                # Track event types for this token
                self.token_activity[token]['event_types'][event_category] = \
                    self.token_activity[token]['event_types'].get(event_category, 0) + 1
            
            # Update collection activity
            if 'collection_name' in event:
                collection = event.get('collection_name')
                if collection not in self.collection_activity:
                    self.collection_activity[collection] = {
                        'total_events': 0,
                        'first_seen': datetime.now().isoformat(),
                        'last_seen': datetime.now().isoformat(),
                        'event_types': {}
                    }
                
                self.collection_activity[collection]['total_events'] += 1
                self.collection_activity[collection]['last_seen'] = datetime.now().isoformat()
                
                # Track event types for this collection
                self.collection_activity[collection]['event_types'][event_category] = \
                    self.collection_activity[collection]['event_types'].get(event_category, 0) + 1
            
            # Update time-based metrics
            current_hour = datetime.now().hour
            self.hourly_event_counts[current_hour] += 1
            
            current_day = datetime.now().weekday()
            self.daily_event_counts[current_day] += 1
            
            # Update version history every minute
            if time.time() - self.last_metrics_update > 60:
                self.version_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'version': self.last_processed_version
                })
                
                # Keep only the last 1440 entries (24 hours at 1 per minute)
                if len(self.version_history) > 1440:
                    self.version_history = self.version_history[-1440:]
                    
                self.last_metrics_update = time.time()
                
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    def is_user_related_event(self, event):
        """Check if an event is related to user-monitored accounts, tokens, or collections.
        
        Args:
            event: The event to check
            
        Returns:
            bool: True if the event is related to user-monitored items, False otherwise
        """
        # If no monitored items are set, consider all events as user-related
        if not self.monitored_accounts and not self.monitored_tokens and not self.monitored_collections:
            return True
            
        # Check if event involves monitored accounts
        if event.get('account') and event['account'] in self.monitored_accounts:
            return True
            
        # Check if event involves monitored tokens
        if event.get('token_name') and event['token_name'] in self.monitored_tokens:
            return True
            
        # Check if event involves monitored collections
        if event.get('collection_name') and event['collection_name'] in self.monitored_collections:
            return True
            
        # Check if event data contains monitored accounts
        if event.get('data'):
            data = event['data']
            
            # Check for creator address
            if data.get('creator_address') and data['creator_address'] in self.monitored_accounts:
                return True
                
            # Check for sender and receiver in transfers
            if data.get('sender') and data['sender'] in self.monitored_accounts:
                return True
                
            if data.get('receiver') and data['receiver'] in self.monitored_accounts:
                return True
                
            # Check for token name in token events
            if data.get('token_name') and data['token_name'] in self.monitored_tokens:
                return True
                
            # Check for collection name in collection events
            if data.get('collection_name') and data['collection_name'] in self.monitored_collections:
                return True
                
        return False
    
    def _enrich_event(self, event):
        """Enrich an event with additional context and information.
        
        Args:
            event: The event to enrich
            
        Returns:
            dict: Enriched event with additional context
        """
        try:
            # Create a copy of the event to avoid modifying the original
            enriched = event.copy() if isinstance(event, dict) else event
            
            # Add timestamp if not present
            if 'timestamp' not in enriched:
                enriched['timestamp'] = datetime.now().isoformat()
                
            # Add event type if not present
            if 'event_type' not in enriched:
                event_handle = enriched.get('event_handle', '')
                field_name = enriched.get('field_name', '')
                enriched['event_type'] = f"{event_handle}/{field_name}"
            
            # Simplify event type for better readability
            if 'event_type' in enriched:
                event_type = enriched['event_type']
                if '::token::TokenStore/deposit_events' in event_type:
                    enriched['event_category'] = 'token_deposit'
                elif '::token::TokenStore/withdraw_events' in event_type:
                    enriched['event_category'] = 'token_withdrawal'
                elif 'coin::CoinStore' in event_type:
                    enriched['event_category'] = 'coin_transfer'
                else:
                    enriched['event_category'] = 'other'
            
            # Add transaction URL
            if 'version' in enriched:
                tx_version = enriched['version']
                enriched['transaction_url'] = f"{self.explorer_url}/txn/{tx_version}"
                
            # Add account URL
            if 'account' in enriched:
                account = enriched['account']
                enriched['account_url'] = f"{self.explorer_url}/account/{account}"
            
            # Extract and simplify data for better UI display
            simplified_data = {}
            data = enriched.get('data', {})
            
            if isinstance(data, dict):
                # Extract token information if present in data
                if 'id' in data:
                    token_id = data['id']
                    if isinstance(token_id, dict) and 'token_data_id' in token_id:
                        token_data_id = token_id['token_data_id']
                        
                        # Extract collection and token names
                        if 'collection' in token_data_id:
                            simplified_data['collection'] = token_data_id['collection']
                            enriched['collection_name'] = token_data_id['collection']
                        if 'name' in token_data_id:
                            simplified_data['token_name'] = token_data_id['name']
                            enriched['token_name'] = token_data_id['name']
                
                # Extract amount if present
                if 'amount' in data:
                    simplified_data['amount'] = data['amount']
                    enriched['amount'] = data['amount']
                    
                    # Convert amount to APT for coin transfers
                    if enriched.get('event_category') == 'coin_transfer':
                        try:
                            amount_apt = float(data['amount']) / 100000000  # 8 decimal places for APT
                            enriched['amount_apt'] = amount_apt
                        except:
                            pass
                
                # Extract other useful fields
                for key in ['type', 'from', 'to', 'creator']:
                    if key in data:
                        simplified_data[key] = data[key]
            
            # Replace the complex data with simplified data
            enriched['details'] = simplified_data
            
            # Add a description for the event
            if enriched.get('event_category') == 'token_deposit':
                token_name = enriched.get('token_name', 'token')
                collection = enriched.get('collection_name', 'collection')
                enriched['description'] = f"Token deposit: {token_name} from {collection}"
            elif enriched.get('event_category') == 'token_withdrawal':
                token_name = enriched.get('token_name', 'token')
                collection = enriched.get('collection_name', 'collection')
                enriched['description'] = f"Token withdrawal: {token_name} from {collection}"
            elif enriched.get('event_category') == 'coin_transfer':
                amount_apt = enriched.get('amount_apt', 0)
                enriched['description'] = f"Coin transfer: {amount_apt:.8f} APT"
            else:
                enriched['description'] = f"Blockchain event: {enriched.get('event_type', 'unknown')}"
            
            # Add importance score (all events are now considered significant)
            enriched['importance_score'] = 1.0
            
            # Add a unique ID for the event if not present
            if 'id' not in enriched:
                # Create a unique ID based on event data
                event_str = json.dumps(enriched, sort_keys=True)
                enriched['id'] = hashlib.md5(event_str.encode()).hexdigest()
            
            # Create a clean version of the event with only the most relevant fields
            clean_event = {
                'id': enriched.get('id', ''),
                'event_type': enriched.get('event_type', 'unknown'),
                'event_category': enriched.get('event_category', 'other'),
                'timestamp': enriched.get('timestamp', ''),
                'account': enriched.get('account', ''),
                'version': enriched.get('version', ''),
                'description': enriched.get('description', ''),
                'details': simplified_data,
                'transaction_url': enriched.get('transaction_url', ''),
                'account_url': enriched.get('account_url', '')
            }
            
            # Add token-specific fields if present
            if 'token_name' in enriched:
                clean_event['token_name'] = enriched['token_name']
            if 'collection_name' in enriched:
                clean_event['collection_name'] = enriched['collection_name']
            if 'amount_apt' in enriched:
                clean_event['amount_apt'] = enriched['amount_apt']
            
            # Convert to JSON-serializable format
            # This ensures that the event can be properly sent to the UI
            return json.loads(json.dumps(clean_event, default=str))
            
        except Exception as e:
            logger.error(f"Error enriching event: {str(e)}")
            return event
    
    async def start_monitoring(self):
        """Start monitoring blockchain events."""
        logger.info("Starting blockchain monitoring...")
        
        try:
            # Validate accounts of interest
            valid_accounts = await self.validate_accounts()
            if not valid_accounts:
                logger.warning("No valid accounts to monitor")
                raise Exception("No valid accounts to monitor")
            
            # Discover event handles
            await self.discover_event_handles()
            
            # Check if we have event handles to monitor
            if not self.event_handles:
                logger.warning("No event handles to monitor")
                raise Exception("No event handles to monitor")
                
            # Since WebSocket approach isn't available in the SDK,
            # we'll raise an exception to fall back to polling
            raise Exception("WebSocket monitoring not implemented, falling back to polling")
                
        except Exception as e:
            logger.error(f"Error setting up monitoring: {str(e)}")
            # Signal to the main application that it should fall back to polling
            raise Exception(f"Monitoring setup failed: {str(e)}")
    
    async def poll_for_events_async(self, discord_bot=None):
        """Poll for events from the blockchain asynchronously.
        
        Args:
            discord_bot: Optional DiscordBot instance to post events to
            
        Returns:
            list: List of significant events
        """
        try:
            # Validate accounts if not already done
            if not self.validated_accounts:
                await self.validate_accounts()
                
            # Discover event handles if not already done
            if not self.event_handles:
                await self.discover_event_handles()
            
            # Fetch events from all event handles
            events = await self.fetch_events()
            
            if not events:
                logger.info("No new events detected")
                return []
                
            logger.info(f"Processing {len(events)} events")
            
            # Process events to find significant ones
            significant_events = self.process_events(events, discord_bot)
            
            # Update counters
            self.significant_events_count += len(significant_events)
            
            # Add version to version history
            if time.time() - self.last_metrics_update > 60:
                self.version_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'version': self.last_processed_version
                })
                
                # Keep only the last 1440 entries (24 hours at 1 per minute)
                if len(self.version_history) > 1440:
                    self.version_history = self.version_history[-1440:]
                    
                self.last_metrics_update = time.time()
            
            logger.info(f"Found {len(significant_events)} significant events out of {len(events)} total events")
            return significant_events
            
        except Exception as e:
            logger.error(f"Error polling for events: {str(e)}")
            return []
    
    def poll_for_events(self, discord_bot=None):
        """Poll for events from the blockchain.
        
        Args:
            discord_bot: Optional DiscordBot instance to post events to
            
        Returns:
            list: List of significant events
        """
        try:
            # Use a simple synchronous approach to avoid event loop issues
            import asyncio
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the async method and get the events
                events = loop.run_until_complete(self.poll_for_events_async(discord_bot))
                return events
            finally:
                # Always close the loop to prevent resource leaks
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in poll_for_events: {str(e)}")
            return []
    
    def _is_significant_event(self, event):
        """Determine if an event is significant.
        
        Args:
            event: The event to check
            
        Returns:
            bool: True if the event is significant, False otherwise
        """
        # For now, consider all events significant
        return True
    
    def stop(self):
        """Stop monitoring blockchain events."""
        logger.info("Stopping blockchain monitoring")
        self.running = False
