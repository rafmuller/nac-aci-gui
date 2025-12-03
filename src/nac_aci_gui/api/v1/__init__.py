"""
API v1 Blueprint Registration
"""
from flask import Flask
from .general import general_bp
from .tables import tables_bp
from .admin import admin_bp
from .aci import aci_bp
from .nac import nac_bp
from .netbox import netbox_bp


def register_v1_blueprints(app: Flask):
    """
    Register all v1 API blueprints with the Flask application

    Args:
        app: Flask application instance
    """
    # Register blueprints with /api/v1 prefix
    app.register_blueprint(general_bp, url_prefix='/api/v1')
    app.register_blueprint(tables_bp, url_prefix='/api/v1/tables')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    app.register_blueprint(aci_bp, url_prefix='/api/v1/aci')
    app.register_blueprint(nac_bp, url_prefix='/api/v1/nac')
    app.register_blueprint(netbox_bp, url_prefix='/api/v1/netbox')
