from .main_routes import main_bp
from .auth_routes import auth_bp
from .cart_routes import cart_bp
from .profile_routes import profile_bp
from .admin_routes import admin_bp
from .products import products_bp
from .search import search_bp  # Sửa lại import này để nhất quán với các import khác

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(search_bp)
    

    