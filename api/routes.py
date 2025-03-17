# api/routes.py
from flask import request
from flask_restful import Resource
from utils.logger import get_logger
import asyncio
import time
from datetime import datetime

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
            "timestamp": datetime.now().isoformat()
        }

class EventsResource(Resource):
    """Resource for retrieving blockchain events."""
    
    def get(self):
        """Get recent blockchain events."""
        if not _blockchain_monitor:
            return {"error": "Blockchain monitor not initialized"}, 500
            
        try:
            # Get query parameters for filtering
            event_type = request.args.get('type')
            account = request.args.get('account')
            token = request.args.get('token')
            collection = request.args.get('collection')
            limit = request.args.get('limit', 50, type=int)
            
            # Get recent events from the blockchain monitor
            events = getattr(_blockchain_monitor, 'recent_events', [])
            if not events:
                # If no events are stored, return an empty list
                return {"events": [], "filters_applied": {}}
            
            # Apply filters if provided
            filtered_events = events
            filters_applied = {}
            
            if event_type:
                filtered_events = [e for e in filtered_events if e.get('event_category') == event_type]
                filters_applied['event_type'] = event_type
                
            if account:
                filtered_events = [e for e in filtered_events if e.get('account') == account]
                filters_applied['account'] = account
                
            if token:
                filtered_events = [e for e in filtered_events if e.get('token_name') == token]
                filters_applied['token'] = token
                
            if collection:
                filtered_events = [e for e in filtered_events if e.get('collection_name') == collection]
                filters_applied['collection'] = collection
            
            # Get available filter options from all events
            available_filters = {
                'event_types': list(set(e.get('event_category') for e in events if 'event_category' in e)),
                'accounts': list(set(e.get('account') for e in events if 'account' in e)),
                'tokens': list(set(e.get('token_name') for e in events if 'token_name' in e)),
                'collections': list(set(e.get('collection_name') for e in events if 'collection_name' in e))
            }
            
            # Calculate some statistics
            stats = {
                'total_events': len(events),
                'filtered_events': len(filtered_events),
                'event_type_distribution': {},
                'latest_event_time': max([e.get('timestamp', '2000-01-01T00:00:00') for e in events], default='2000-01-01T00:00:00')
            }
            
            # Calculate event type distribution
            for event in events:
                event_category = event.get('event_category', 'other')
                stats['event_type_distribution'][event_category] = stats['event_type_distribution'].get(event_category, 0) + 1
            
            # Limit the number of events returned
            limited_events = filtered_events[-limit:] if limit > 0 else filtered_events
            
            # Return the events with metadata
            return {
                "events": limited_events,
                "total_count": len(events),
                "filtered_count": len(filtered_events),
                "filters_applied": filters_applied,
                "available_filters": available_filters,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving events: {str(e)}")
            return {"error": str(e)}, 500

class MetricsResource(Resource):
    """Resource for system metrics."""
    
    def get(self):
        """Get system metrics."""
        if not _blockchain_monitor:
            return {"error": "Blockchain monitor not initialized"}, 500
            
        try:
            # Get the latest version synchronously if it's an async method
            latest_version = 0
            get_latest_version_method = getattr(_blockchain_monitor, 'get_latest_version', None)
            
            if get_latest_version_method:
                if asyncio.iscoroutinefunction(get_latest_version_method):
                    # If it's an async function, run it in a new event loop
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        latest_version = loop.run_until_complete(get_latest_version_method())
                        loop.close()
                    except Exception as e:
                        logger.error(f"Error getting latest version: {str(e)}")
                        latest_version = 0
                else:
                    # If it's a regular function, just call it
                    try:
                        latest_version = get_latest_version_method()
                    except Exception as e:
                        logger.error(f"Error getting latest version: {str(e)}")
                        latest_version = 0
            
            # Get recent events for analysis
            recent_events = getattr(_blockchain_monitor, 'recent_events', [])
            
            # Calculate event type distribution
            event_types = {}
            token_activity = {}
            account_activity = {}
            collection_activity = {}
            
            # Last 24 hours timestamp
            last_24h = time.time() - (24 * 60 * 60)
            events_24h = 0
            
            for event in recent_events:
                # Count event types
                event_category = event.get('event_category', 'other')
                event_types[event_category] = event_types.get(event_category, 0) + 1
                
                # Track token activity
                if 'token_name' in event:
                    token_name = event.get('token_name')
                    token_activity[token_name] = token_activity.get(token_name, 0) + 1
                
                # Track account activity
                if 'account' in event:
                    account = event.get('account')
                    account_activity[account] = account_activity.get(account, 0) + 1
                
                # Track collection activity
                if 'collection_name' in event:
                    collection = event.get('collection_name')
                    collection_activity[collection] = collection_activity.get(collection, 0) + 1
                
                # Count events in last 24 hours
                event_time = event.get('timestamp')
                if event_time:
                    try:
                        event_timestamp = datetime.fromisoformat(event_time.replace('Z', '+00:00')).timestamp()
                        if event_timestamp > last_24h:
                            events_24h += 1
                    except:
                        pass
            
            # Sort activity by frequency
            top_tokens = sorted(token_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            top_accounts = sorted(account_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            top_collections = sorted(collection_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Log the metrics values for debugging
            logger.info(f"Events processed: {getattr(_blockchain_monitor, 'events_processed_count', 0)}")
            logger.info(f"Significant events: {getattr(_blockchain_monitor, 'significant_events_count', 0)}")
            logger.info(f"Monitored accounts: {len(getattr(_blockchain_monitor, 'validated_accounts', []))}")
            logger.info(f"Event handles: {len(getattr(_blockchain_monitor, 'event_handles', []))}")
            
            # Get metrics from the blockchain monitor
            metrics = {
                "events_processed": getattr(_blockchain_monitor, 'events_processed_count', 0),
                "significant_events": getattr(_blockchain_monitor, 'significant_events_count', 0),
                "last_processed_version": getattr(_blockchain_monitor, 'last_processed_version', 0),
                "monitored_accounts": len(getattr(_blockchain_monitor, 'validated_accounts', [])),
                "event_handles": len(getattr(_blockchain_monitor, 'event_handles', [])),
                "polling_interval": getattr(_blockchain_monitor, 'polling_interval', 60),
                "uptime": int(time.time() - getattr(_blockchain_monitor, 'start_time', time.time())),
                "account_list": getattr(_blockchain_monitor, 'validated_accounts', []),
                "start_time": getattr(_blockchain_monitor, 'start_time', time.time()),
                "is_monitoring": getattr(_blockchain_monitor, 'running', False),
                "latest_version": latest_version,
                "system_status": {
                    "blockchain_module": "online" if _blockchain_monitor else "offline",
                    "ai_module": "online" if _ai_module else "offline",
                    "discord_bot": "online" if _discord_bot else "offline"
                },
                # Enhanced metrics
                "event_distribution": event_types,
                "events_last_24h": events_24h,
                "top_tokens": dict(top_tokens),
                "top_accounts": dict(top_accounts),
                "top_collections": dict(top_collections),
                "total_events_tracked": len(recent_events),
                "version_delta": latest_version - getattr(_blockchain_monitor, 'last_processed_version', 0) if latest_version > 0 else 0
            }
            
            # Add detailed metrics from the blockchain monitor if available
            if hasattr(_blockchain_monitor, 'event_type_counts'):
                metrics["detailed_event_types"] = getattr(_blockchain_monitor, 'event_type_counts', {})
                
            if hasattr(_blockchain_monitor, 'account_activity'):
                # Get top 10 accounts by activity
                account_data = getattr(_blockchain_monitor, 'account_activity', {})
                top_accounts_detailed = sorted(
                    account_data.items(), 
                    key=lambda x: x[1]['total_events'] if isinstance(x[1], dict) and 'total_events' in x[1] else 0, 
                    reverse=True
                )[:10]
                metrics["detailed_account_activity"] = dict(top_accounts_detailed)
                
            if hasattr(_blockchain_monitor, 'token_activity'):
                # Get top 10 tokens by activity
                token_data = getattr(_blockchain_monitor, 'token_activity', {})
                top_tokens_detailed = sorted(
                    token_data.items(), 
                    key=lambda x: x[1]['total_events'] if isinstance(x[1], dict) and 'total_events' in x[1] else 0, 
                    reverse=True
                )[:10]
                metrics["detailed_token_activity"] = dict(top_tokens_detailed)
                
            if hasattr(_blockchain_monitor, 'collection_activity'):
                # Get top 10 collections by activity
                collection_data = getattr(_blockchain_monitor, 'collection_activity', {})
                top_collections_detailed = sorted(
                    collection_data.items(), 
                    key=lambda x: x[1]['total_events'] if isinstance(x[1], dict) and 'total_events' in x[1] else 0, 
                    reverse=True
                )[:10]
                metrics["detailed_collection_activity"] = dict(top_collections_detailed)
                
            if hasattr(_blockchain_monitor, 'hourly_event_counts'):
                metrics["hourly_event_counts"] = getattr(_blockchain_monitor, 'hourly_event_counts', [0] * 24)
                
            if hasattr(_blockchain_monitor, 'daily_event_counts'):
                metrics["daily_event_counts"] = getattr(_blockchain_monitor, 'daily_event_counts', [0] * 7)
                
            if hasattr(_blockchain_monitor, 'version_history'):
                # Get the last 60 entries (1 hour at 1 per minute)
                version_history = getattr(_blockchain_monitor, 'version_history', [])
                metrics["version_history"] = version_history[-60:] if version_history else []
            
            # Use datetime.now() directly instead of asyncio.to_thread
            return {
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {str(e)}")
            return {"error": str(e)}, 500

class ControlResource(Resource):
    """Resource for controlling the blockchain monitor."""
    
    def post(self):
        """Control the blockchain monitor."""
        if not _blockchain_monitor:
            return {"error": "Blockchain monitor not initialized"}, 500
            
        data = request.get_json()
        if not data:
            return {"error": "No data provided"}, 400
            
        action = data.get("action")
        if not action:
            return {"error": "No action specified"}, 400
            
        try:
            result = {"success": False, "message": "Unknown action"}
            
            if action == "start":
                # Start monitoring if not already running
                if not getattr(_blockchain_monitor, 'running', False):
                    # This would normally be handled by the main application
                    # Here we'll just update the status
                    setattr(_blockchain_monitor, 'running', True)
                    result = {"success": True, "message": "Monitoring started"}
                else:
                    result = {"success": False, "message": "Already running"}
                    
            elif action == "stop":
                # Stop monitoring if running
                if getattr(_blockchain_monitor, 'running', False):
                    # This would normally be handled by the main application
                    # Here we'll just update the status
                    setattr(_blockchain_monitor, 'running', False)
                    result = {"success": True, "message": "Monitoring stopped"}
                else:
                    result = {"success": False, "message": "Not running"}
                    
            elif action == "update_interval":
                # Update polling interval
                interval = data.get("interval")
                if interval and isinstance(interval, int) and interval > 0:
                    setattr(_blockchain_monitor, 'polling_interval', interval)
                    result = {"success": True, "message": f"Polling interval updated to {interval} seconds"}
                else:
                    result = {"success": False, "message": "Invalid interval"}
                    
            return result
            
        except Exception as e:
            logger.error(f"Error controlling blockchain monitor: {str(e)}")
            return {"error": str(e)}, 500

class TestEventsResource(Resource):
    """Resource for adding test events."""
    
    def post(self):
        """Add test events to the blockchain monitor and send to Discord."""
        if not _blockchain_monitor or not _discord_bot:
            return {"error": "Blockchain monitor or Discord bot not initialized"}, 500
            
        try:
            data = request.get_json()
            if not data or not isinstance(data, list):
                return {"error": "Invalid data format. Expected a list of events."}, 400
            
            # Add events to blockchain monitor's recent_events
            _blockchain_monitor.recent_events = data
            
            # Update metrics
            _blockchain_monitor.events_processed_count += len(data)
            
            # Update event type counts
            for event in data:
                event_category = event.get('event_category', 'other')
                if not hasattr(_blockchain_monitor, 'event_type_counts'):
                    _blockchain_monitor.event_type_counts = {}
                _blockchain_monitor.event_type_counts[event_category] = _blockchain_monitor.event_type_counts.get(event_category, 0) + 1
            
            # Send only one event to Discord (the most recent one)
            sent_count = 0
            if data:
                try:
                    # Get the most recent event (last in the list)
                    most_recent_event = data[-1]
                    
                    # Post event to Discord
                    _discord_bot.post_blockchain_event(most_recent_event)
                    sent_count = 1
                    logger.info(f"Posted most recent event to Discord: {most_recent_event.get('event_category', 'unknown')}")
                    
                    # Update significant events count
                    _blockchain_monitor.significant_events_count += 1
                except Exception as e:
                    logger.error(f"Error posting event to Discord: {str(e)}")
            
            return {
                "success": True,
                "message": f"Added {len(data)} test events",
                "event_count": len(data),
                "sent_to_discord": sent_count
            }
            
        except Exception as e:
            logger.error(f"Error adding test events: {str(e)}")
            return {"error": str(e)}, 500

class PageLoadResource(Resource):
    """Resource for handling page load events."""
    
    # Keep track of the last posted event ID to avoid duplicates
    last_posted_event_id = None
    
    def post(self):
        """Handle page load event and send a single event to Discord."""
        if not _blockchain_monitor or not _discord_bot:
            return {"error": "Blockchain monitor or Discord bot not initialized"}, 500
            
        try:
            # Get the most recent event from the blockchain monitor
            recent_events = getattr(_blockchain_monitor, 'recent_events', [])
            
            if recent_events:
                # Get the most recent event
                most_recent_event = recent_events[-1]
                
                # Check if this event has already been posted
                event_id = most_recent_event.get('id', '')
                if event_id == PageLoadResource.last_posted_event_id:
                    return {
                        "success": True,
                        "message": "Event already posted, skipping duplicate",
                        "event": most_recent_event
                    }
                
                # Post event to Discord
                _discord_bot.post_blockchain_event(most_recent_event)
                logger.info(f"Posted most recent event to Discord on page load: {most_recent_event.get('event_category', 'unknown')}")
                
                # Update the last posted event ID
                PageLoadResource.last_posted_event_id = event_id
                
                return {
                    "success": True,
                    "message": "Posted most recent event to Discord",
                    "event": most_recent_event
                }
            else:
                return {
                    "success": False,
                    "message": "No events available to post"
                }
            
        except Exception as e:
            logger.error(f"Error handling page load event: {str(e)}")
            return {"error": str(e)}, 500

class DiscordTestResource(Resource):
    """Resource for testing Discord connection."""
    
    def post(self):
        """Test the Discord connection by sending a test message."""
        if not _discord_bot:
            return {"error": "Discord bot not initialized"}, 500
            
        try:
            # Test the Discord connection
            success = _discord_bot.test_discord_connection()
            
            if success:
                return {
                    "success": True,
                    "message": "Discord test message sent successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to send Discord test message. Check logs for details."
                }
            
        except Exception as e:
            logger.error(f"Error testing Discord connection: {str(e)}")
            return {"error": str(e)}, 500

def register_routes(api):
    """Register API routes."""
    api.add_resource(EventResource, '/api/event')
    api.add_resource(MemeResource, '/api/meme')
    api.add_resource(QuestionResource, '/api/question')
    api.add_resource(StatusResource, '/api/status')
    api.add_resource(EventsResource, '/api/events')
    api.add_resource(MetricsResource, '/api/metrics')
    api.add_resource(ControlResource, '/api/control')
    api.add_resource(TestEventsResource, '/api/test_events')
    api.add_resource(PageLoadResource, '/api/page_load')
    api.add_resource(DiscordTestResource, '/api/test_discord')
    logger.info("API routes registered")
