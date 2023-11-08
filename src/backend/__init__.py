"""
Methods and objects pertaining to the backend database.
"""

# =============================================================================

from flask_migrate import Migrate

from backend import friend, models, user
from backend.models import db

# =============================================================================

__all__ = (
    "db",
    "models",
    "user",
    "friend",
)

# =============================================================================


def init_app(app):
    db.init_app(app)
    Migrate(app, db)
