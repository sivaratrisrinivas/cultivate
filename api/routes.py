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
            "timestamp": asyncio.run(asyncio.to_thread(lambda: datetime.now().isoformat()))
        }

class EventsResource(Resource):
    """Resource for retrieving blockchain events."""
    
    def get(self):
        """Get recent blockchain events."""
        if not _blockchain_monitor:
            return {"error": "Blockchain monitor not initialized"}, 500
            
        try:
            # Get recent events from the blockchain monitor
            # We'll limit to the last 50 events for performance
            events = getattr(_blockchain_monitor, 'recent_events', [])
            if not events:
                # If no events are stored, return an empty list
                return {"events": []}
                
            # Return the events
            return {
                "events": events[-50:],  # Last 50 events
                "total_count": len(events),
                "timestamp": asyncio.run(asyncio.to_thread(lambda: datetime.now().isoformat()))
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
                "latest_version": getattr(_blockchain_monitor, 'get_latest_version', lambda: 0)(),
                "system_status": {
                    "blockchain_module": "online" if _blockchain_monitor else "offline",
                    "ai_module": "online" if _ai_module else "offline",
                    "discord_bot": "online" if _discord_bot else "offline"
                }
            }
            
            return {
                "metrics": metrics,
                "timestamp": asyncio.run(asyncio.to_thread(lambda: datetime.now().isoformat()))
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

def register_routes(api):
    """Register API routes."""
    api.add_resource(EventResource, '/api/event')
    api.add_resource(MemeResource, '/api/meme')
    api.add_resource(QuestionResource, '/api/question')
    api.add_resource(StatusResource, '/api/status')
    api.add_resource(EventsResource, '/api/events')
    api.add_resource(MetricsResource, '/api/metrics')
    api.add_resource(ControlResource, '/api/control')
    logger.info("API routes registered")
