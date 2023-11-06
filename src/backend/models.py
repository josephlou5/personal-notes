"""
The database and models.
"""

# =============================================================================

import re
from datetime import datetime
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

# =============================================================================

db = SQLAlchemy()

# =============================================================================

USERNAME_PATTERN = re.compile(r"[a-zA-Z0-9_.]{3,30}")

MAX_NOTE_LENGTH = 10000

# =============================================================================


class User(db.Model):
    """A user."""

    __tablename__ = "Users"

    id = Column(Integer, primary_key=True)
    email = Column(String(), unique=True, nullable=False)
    username = Column(String(30), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    is_admin = Column(Boolean(), nullable=False, default=False)
    is_deleted = Column(Boolean(), nullable=False, default=False)

    def __init__(
        self,
        email: str,
        username: str,
        display_name: str,
        is_deleted: bool = False,
    ):
        if not 3 <= len(username) <= 30:
            raise ValueError("Username must be between 3 and 30 characters")
        if not 1 <= len(display_name) <= 100:
            raise ValueError(
                "Display name must be between 1 and 100 characters"
            )
        if USERNAME_PATTERN.fullmatch(username) is None:
            raise ValueError(
                "Username must only consist of letters, numbers, underscore, "
                "or period."
            )
        self.email = email
        self.username = username
        self.display_name = display_name
        self.is_deleted = is_deleted


class Friendship(db.Model):
    """A friendship between two users."""

    __tablename__ = "Friendships"

    user1_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    user2_id = Column(Integer, ForeignKey(User.id), primary_key=True)

    def __init__(self, user1_id: int, user2_id: int):
        if user1_id == user2_id:
            raise ValueError("Cannot be friends with yourself")
        # Sort the IDs so that friendships are always unique
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        self.user1_id = user1_id
        self.user2_id = user2_id


class FriendRequest(db.Model):
    """A request to be friends with another user.

    This table only contains active requests.
    """

    __tablename__ = "FriendRequests"

    sender_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    recipient_id = Column(Integer, ForeignKey(User.id), primary_key=True)

    def __init__(self, sender_id: int, recipient_id: int):
        if sender_id == recipient_id:
            raise ValueError("Cannot be friends with yourself")
        self.sender_id = sender_id
        self.recipient_id = recipient_id


class FriendNickname(db.Model):
    """A nickname for a user's friend.

    This table only contains set nicknames. That is, if a user clears a
    nickname for their friend, the row will be deleted.
    """

    __tablename__ = "FriendNicknames"

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    friend_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    nickname = Column(String(100), nullable=False)

    def __init__(self, user_id: int, friend_id: int, nickname: str):
        if user_id == friend_id:
            raise ValueError("Cannot be friends with yourself")
        if not 1 <= len(nickname) <= 100:
            raise ValueError("Nickname must be between 1 and 100 characters")
        self.user_id = user_id
        self.friend_id = friend_id
        self.nickname = nickname


class DraftNote(db.Model):
    """A draft note."""

    __tablename__ = "DraftNotes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    # Nullable, since a draft doesn't need a recipient yet
    recipient_id = Column(Integer, ForeignKey(User.id))
    text = Column(String(MAX_NOTE_LENGTH), nullable=False, default="")

    def __init__(
        self, user_id: int, recipient_id: Optional[int] = None, text: str = ""
    ):
        if user_id == recipient_id:
            raise ValueError("Cannot send note to yourself")
        if len(text) > MAX_NOTE_LENGTH:
            raise ValueError("Max note length exceeded")
        self.user_id = user_id
        self.recipient_id = recipient_id
        self.text = text


class Note(db.Model):
    """A note."""

    __tablename__ = "Notes"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey(User.id), nullable=False)
    recipient_id = Column(Integer, ForeignKey(User.id), nullable=False)
    text = Column(String(MAX_NOTE_LENGTH), nullable=False, default="")
    time_sent = Column(DateTime(timezone=False), nullable=False)

    def __init__(
        self,
        sender_id: int,
        recipient_id: Optional[int] = None,
        text: str = "",
    ):
        if sender_id == recipient_id:
            raise ValueError("Cannot send note to yourself")
        if len(text) > MAX_NOTE_LENGTH:
            raise ValueError("Max note length exceeded")
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.text = text
        self.time_sent = datetime.utcnow()


class FavoriteNote(db.Model):
    """A note that a user has marked as favorite."""

    __tablename__ = "FavoriteNotes"

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    note_id = Column(Integer, ForeignKey(Note.id), primary_key=True)

    def __init__(self, user_id: int, note_id: int):
        self.user_id = user_id
        self.note_id = note_id


class DeletedNotes(db.Model):
    """A note that has been deleted by a user."""

    __tablename__ = "DeletedNotes"

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    note_id = Column(Integer, ForeignKey(Note.id), primary_key=True)

    def __init__(self, user_id: int, note_id: int):
        self.user_id = user_id
        self.note_id = note_id
