"""
Backend utilities.
"""

# =============================================================================

from backend.models import db

# =============================================================================

__all__ = (
    "query",
    "_exists",
)

# =============================================================================


def query(model, filter_condition):
    return db.session.scalars(db.select(model).filter(filter_condition))


def _exists(model, filter_condition) -> bool:
    """Returns whether a row exists that matches the given condition."""
    return query(model, filter_condition).first() is not None
