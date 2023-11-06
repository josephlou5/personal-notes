"""
Methods and objects pertaining to the backend database.
"""

# =============================================================================

from flask_migrate import Migrate

from backend import models, user
from backend.models import db

# =============================================================================

__all__ = (
    "db",
    "models",
    "user",
)

# =============================================================================


def init_app(app):
    db.init_app(app)
    Migrate(app, db)
