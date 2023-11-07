"""
Helper methods for Users.
"""

# =============================================================================

from typing import List, Optional

from sqlalchemy import select, union

from backend._utils import query
from backend.models import Friendship, User, db

# =============================================================================


def _exists(filter_condition) -> bool:
    """Returns whether a user exists that matches the given condition."""
    return query(User, filter_condition).first() is not None


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

    if _exists(User.username == user.username):
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
        if _exists(User.username == username):
            raise ValueError(f'Username "{username}" is already taken')
        changed = True
        user.username = username

    if display_name != user.display_name:
        changed = True
        user.display_name = display_name

    if changed:
        db.session.commit()

    return user


# =============================================================================


def get_friend_usernames(user_id: int) -> List[str]:
    """Returns the usernames of the requested user's friends.

    The usernames will be sorted alphabetically.
    """
    return sorted(
        db.session.scalars(
            union(
                select(User.username)
                .select_from(Friendship)
                .join(User, User.id == Friendship.user2_id)
                .where(Friendship.user1_id == user_id),
                select(User.username)
                .select_from(Friendship)
                .join(User, User.id == Friendship.user1_id)
                .where(Friendship.user2_id == user_id),
            )
        ).all()
    )
