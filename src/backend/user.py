"""
Helper methods for Users.
"""

# =============================================================================

from typing import Optional

from backend.models import User, db

# =============================================================================


def _exists(filter_condition) -> bool:
    """Returns whether a user exists that matches the given condition."""
    return User.query.filter(filter_condition).first() is not None


# =============================================================================


def get_by_email(email: str) -> Optional[User]:
    """Returns the requested user, or returns None if they don't exist."""
    return User.query.filter(User.email == email).first()


# =============================================================================


def create(email: str, username: str, display_name: str) -> User:
    """Creates the user with the given info.

    Errors are raised if the args were invalid in any way.
    """
    user = User(email, username, display_name)

    if _exists(User.username == user.username):
        raise ValueError(f'Username "{user.username}" is already taken')

    db.session.add(user)
    db.session.commit()
    return user
