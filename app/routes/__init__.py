from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.main import main_bp
from app.routes.nurse import nurse_bp

# Expose blueprints for use in app/__init__.py
__all__ = ['auth_bp', 'admin_bp', 'main_bp', 'nurse_bp']
