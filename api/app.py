# api/app.py
from flask import Flask
from flask_restful import Api
from utils.logger import get_logger

logger = get_logger(__name__)

def create_app(config):
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder='static', static_url_path='')
    
    # Configure Flask app
    app.config['ENV'] = 'development' if config.API.get('DEBUG', False) else 'production'
    
    # Initialize API
    api = Api(app)
    
    # Import routes here to avoid circular imports
    from api.routes import register_routes
    register_routes(api)
    
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    @app.route('/api/info')
    def api_info():
        return {
            "service": "Aptos Social Media Manager",
            "status": "operational",
            "version": "1.0.0"
        }
    
    logger.info("API application created")
    return app
