from flask import Flask
from app.config import Config
from app.routes import auth_bp, admin_bp, main_bp  # Import the blueprints

def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)
    app.config.from_object(Config)  # Load config settings from Config class

    # Register blueprints from app.routes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)

    return app
