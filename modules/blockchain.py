import json
import logging
import time
import threading
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

# Import the Aptos SDK
from aptos_sdk.client import RestClient
from aptos_sdk.account import Account
from aptos_sdk.transactions import EntryFunction, TransactionArgument, TransactionPayload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.last_processed_version = self._get_last_processed_version()
        
        # Metrics for UI
        self.start_time = time.time()
        self.events_processed_count = 0
        self.significant_events_count = 0
        self.recent_events = []  # Store recent events for UI display
        self.polling_interval = 60  # Default polling interval in seconds
        self.explorer_url = "https://explorer.aptoslabs.com"
        
        # Monitored accounts, tokens, and collections
        self.monitored_accounts = []
        self.monitored_tokens = []
        self.monitored_collections = []
        
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
            return 0
            
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
    
    def validate_accounts(self):
        """Validate that the accounts of interest exist on the blockchain."""
        valid_accounts = []
        
        for account in self.accounts_of_interest:
            try:
                # Use the Aptos SDK to fetch account information
                account_info = self.client.account(account)
                if account_info:
                    logger.info(f"Account validated: {account}")
                    valid_accounts.append(account)
                else:
                    logger.warning(f"Account not found: {account}")
            except Exception as e:
                logger.warning(f"Account {account} not found: {str(e)}")
                
        self.validated_accounts = valid_accounts
        return valid_accounts
    
    def discover_event_handles(self):
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
                    # Try to fetch events for this handle to see if it exists
                    # Note: The SDK doesn't have a direct way to check if a handle exists,
                    # so we'll try to fetch events and catch exceptions
                    resource_type = handle_info["handle"]
                    field_name = handle_info["field"]
                    
                    # Get the resource that contains the event handle
                    try:
                        # Try to get the resource directly
                        resource = self.client.account_resource(
                            account,
                            resource_type
                        )
                        
                        # Check if the field exists in the resource
                        if field_name in resource["data"]:
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
    
    def fetch_events(self):
        """Fetch events from the blockchain using the Aptos SDK."""
        all_events = []
        current_version = self.get_latest_version()
        
        if current_version <= self.last_processed_version:
            logger.info(f"No new blocks since last check (current: {current_version}, last: {self.last_processed_version})")
            return []
        
        logger.info(f"Fetching events from version {self.last_processed_version} to {current_version}")
        
        # Fetch events for each discovered event handle
        for handle in self.event_handles:
            try:
                # The SDK doesn't have a direct method to get events by version range
                # So we'll need to use the REST API directly or adapt our approach
                
                # For now, we'll try to get recent events and filter them
                try:
                    # Get the resource that contains the event handle
                    resource = self.client.account_resource(
                        handle["account"],
                        handle["event_handle"]
                    )
                    
                    # Get the event handle data
                    if handle["field_name"] in resource["data"]:
                        event_handle = resource["data"][handle["field_name"]]
                        
                        # Get the creation number and counter
                        creation_number = event_handle.get("creation_number", "0")
                        counter = event_handle.get("counter", "0")
                        
                        # If there are events (counter > 0), fetch them
                        if int(counter) > 0:
                            # Use the REST API directly through the client
                            # We'll fetch the most recent events (up to 25)
                            url = f"{self.node_url}/accounts/{handle['account']}/events/{handle['event_handle']}/{handle['field_name']}"
                            response = self.client.client.get(url)
                            events_data = response.json()
                            
                            if events_data:
                                logger.info(f"Found {len(events_data)} events for {handle['account']}/{handle['event_handle']}/{handle['field_name']}")
                                
                                # Store all events regardless of version for UI display
                                for event in events_data:
                                    # Enrich event with handle information
                                    event["account"] = handle["account"]
                                    event["event_handle"] = handle["event_handle"]
                                    event["field_name"] = handle["field_name"]
                                    
                                    # Add to all events list
                                    all_events.append(event)
                                
                                # Add these events to recent_events for UI display
                                enriched_events = [self._enrich_event(event) for event in events_data]
                                self.recent_events.extend(enriched_events)
                                self.recent_events = self.recent_events[-100:]  # Keep only the last 100 events
                except Exception as e:
                    logger.error(f"Error fetching events for {handle['account']}/{handle['event_handle']}/{handle['field_name']}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing handle {handle['account']}/{handle['event_handle']}/{handle['field_name']}: {str(e)}")
        
        # Update the last processed version
        if all_events:
            self._save_last_processed_version(current_version)
            self.last_processed_version = current_version
            
        return all_events
    
    def get_latest_version(self):
        """Get the latest version (block height) of the blockchain."""
        try:
            ledger_info = self.client.info()
            return int(ledger_info["ledger_version"])
        except Exception as e:
            logger.error(f"Error getting latest version: {str(e)}")
            return 0
    
    def process_events(self, events, discord_bot=None):
        """Process a list of events.
        
        Args:
            events (list): List of events to process
            discord_bot: Optional DiscordBot instance to post events to
        """
        if not events:
            return
            
        logger.info(f"Processing {len(events)} events")
        
        for event in events:
            try:
                # Get event type
                event_type = event.get('type', 'unknown')
                logger.info(f"Processing event: {event_type}")
                
                # Enrich event with additional information
                enriched_event = self._enrich_event(event)
                
                # Store event
                self.recent_events.append(enriched_event)
                
                # Limit events list size
                if len(self.recent_events) > 100:
                    self.recent_events = self.recent_events[-100:]
                
                # Check if this event is related to a monitored account
                is_user_related = self.is_user_related_event(enriched_event)
                
                # Only send to Discord if it's related to a user-monitored account
                if is_user_related and discord_bot:
                    discord_bot.post_blockchain_event(enriched_event)
                    
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                
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
                    enriched['event_type'] = 'token_deposit'
                elif '::token::TokenStore/withdraw_events' in event_type:
                    enriched['event_type'] = 'token_withdrawal'
                elif 'coin::CoinStore' in event_type:
                    enriched['event_type'] = 'coin_transfer'
            
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
                
                # Extract other useful fields
                for key in ['type', 'from', 'to', 'creator']:
                    if key in data:
                        simplified_data[key] = data[key]
            
            # Replace the complex data with simplified data
            enriched['details'] = simplified_data
            
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
                'timestamp': enriched.get('timestamp', ''),
                'account': enriched.get('account', ''),
                'version': enriched.get('version', ''),
                'details': simplified_data,
                'transaction_url': enriched.get('transaction_url', ''),
                'account_url': enriched.get('account_url', '')
            }
            
            # Convert to JSON-serializable format
            # This ensures that the event can be properly sent to the UI
            return json.loads(json.dumps(clean_event, default=str))
            
        except Exception as e:
            logger.error(f"Error enriching event: {str(e)}")
            return event
    
    def start_monitoring(self):
        """Start monitoring blockchain events."""
        logger.info("Starting blockchain monitoring...")
        
        try:
            # Validate accounts of interest
            valid_accounts = self.validate_accounts()
            if not valid_accounts:
                logger.warning("No valid accounts to monitor")
                raise Exception("No valid accounts to monitor")
            
            # Discover event handles
            self.discover_event_handles()
            
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
    
    def poll_for_events(self, discord_bot=None):
        """Poll for events from the blockchain.
        
        Args:
            discord_bot: Optional DiscordBot instance to post events to
            
        Returns:
            list: List of significant events
        """
        try:
            # Validate accounts if not already done
            if not self.validated_accounts:
                self.validate_accounts()
                
            # Discover event handles if not already done
            if not self.event_handles:
                self.discover_event_handles()
            
            # Fetch events from all event handles
            events = self.fetch_events()
            
            if not events:
                logger.info("No new events detected")
                return []
                
            logger.info(f"Processing {len(events)} events")
            
            # Process events to find significant ones
            significant_events = []
            processed_events = []
            
            # Process each event
            for event in events:
                # Increment total events counter
                self.events_processed_count += 1
                
                # Check if event is significant
                is_significant = self._is_significant_event(event)
                
                # Enrich event with additional context
                enriched_event = self._enrich_event(event)
                
                # Add to processed events list
                processed_events.append(enriched_event)
                
                # If significant, add to list and increment counter
                if is_significant:
                    significant_events.append(enriched_event)
                    self.significant_events_count += 1
                    
                    # Post to Discord if bot is provided
                    if discord_bot:
                        discord_bot.post_blockchain_event(enriched_event)
            
            # Update recent events list with all processed events
            # Note: We already added events in fetch_events, so we don't need to do it again here
            
            logger.info(f"Found {len(significant_events)} significant events out of {len(processed_events)} total events")
            return significant_events
            
        except Exception as e:
            logger.error(f"Error polling for events: {str(e)}")
            return []
    
    def stop(self):
        """Stop monitoring blockchain events."""
        logger.info("Stopping blockchain monitoring")
        self.running = False
