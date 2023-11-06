"""
All the views for the app.
"""

# =============================================================================

from views import auth, shared, user

# =============================================================================


def register_all(app):
    """Registers all the defined routes to the app."""

    for module in (
        shared,
        auth,
        user,
    ):
        module.app.register(app)
