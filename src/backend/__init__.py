"""
Methods and objects pertaining to the backend database.
"""

# =============================================================================

from flask_migrate import Migrate

from backend.models import db

# =============================================================================

__all__ = ("db",)

# =============================================================================


def init_app(app):
    db.init_app(app)
    Migrate(app, db)
