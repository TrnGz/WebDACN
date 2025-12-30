from flask import Flask
import os
from config import Config
from routes import register_blueprints
from utils.database import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Register all blueprints
    register_blueprints(app)
    
    # Add context processor for template compatibility
    @app.context_processor
    def inject_template_vars():
        return {
            'url_for': url_for_wrapper
        }
    
    return app

def url_for_wrapper(endpoint, **values):
    """Wrapper for url_for to handle old route names"""
    from flask import url_for as flask_url_for
    
    # Map old route names to new ones
    route_mapping = {
        'root': 'main.root',
        'logout': 'auth.logout',
        'loginForm': 'auth.loginForm',
        'cart': 'cart.cart',
        'profileHome': 'profile.profileHome',
        'search': 'search.search',  # Map search route
        'displayCategory': 'search.search_by_category'  # Map category display
    }
    
    # Use mapped route if exists, otherwise use original
    mapped_endpoint = route_mapping.get(endpoint, endpoint)
    
    try:
        return flask_url_for(mapped_endpoint, **values)
    except:
        # Fallback to original if mapping fails
        try:
            return flask_url_for(endpoint, **values)
        except:
            # If all fails, return a safe default
            return '#'

if __name__ == '__main__':
    app = create_app()

    # Initialize database if it doesn't exist
    if not os.path.exists('database.db'):
        init_db()

    app.run(debug=True)
