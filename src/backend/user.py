"""
Helper methods for Users.
"""

# =============================================================================

from typing import Optional

from backend._utils import _exists, query
from backend.models import User, db

# =============================================================================


def get(user_id: int) -> Optional[User]:
    """Returns the requested user, or returns None if they don't exist."""
    return query(User, User.id == user_id).one_or_none()


def get_by_email(email: str) -> Optional[User]:
    """Returns the requested user, or returns None if they don't exist."""
    return query(User, User.email == email).one_or_none()


def get_by_username(username: str) -> Optional[User]:
    """Returns the requested user, or returns None if they don't exist."""
    return query(User, User.username == username).one_or_none()


# =============================================================================


def create(email: str, username: str, display_name: str) -> User:
    """Creates the user with the given info.

    Errors are raised if the args were invalid in any way.
    """
    user = User(email, username, display_name)

    if _exists(User, User.username == user.username):
        raise ValueError(f'Username "{user.username}" is already taken')

    db.session.add(user)
    db.session.commit()
    return user


def edit(user: User, username: str, display_name: str) -> User:
    """Edits the user with the given info.

    Errors are raised if the args were invalid in any way.
    """
    changed = False

    if username != user.username:
        if _exists(User, User.username == username):
            raise ValueError(f'Username "{username}" is already taken')
        changed = True
        user.set_username(username)

    if display_name != user.display_name:
        changed = True
        user.set_display_name(display_name)

    if changed:
        db.session.commit()

    return user
