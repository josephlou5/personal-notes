"""
All the views for the app.
"""

# =============================================================================

from views import auth, shared

# =============================================================================


def register_all(app):
    """Registers all the defined routes to the app."""

    for module in (
        shared,
        auth,
    ):
        module.app.register(app)
