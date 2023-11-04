"""
Helper methods for Users.
"""

# =============================================================================

from typing import Optional

from backend.models import User

# =============================================================================


def get_by_email(email) -> Optional[User]:
    """Returns the requested user, or returns None if they don't exist."""
    return User.query.filter(User.email == email).first()


# =============================================================================


def is_admin_email(email) -> bool:
    user = get_by_email(email)
    if user is None:
        return False
    return user.is_admin
