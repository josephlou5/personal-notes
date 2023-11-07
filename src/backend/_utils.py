"""
Backend utilities.
"""

# =============================================================================

from backend.models import db

# =============================================================================


def query(model, filter_condition):
    return db.session.scalars(db.select(model).filter(filter_condition))
