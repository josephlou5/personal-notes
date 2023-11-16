"""
The database and models.
"""

# =============================================================================

import re
from datetime import datetime
from typing import Dict, Optional

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
        self.email = email
        self.set_username(username)
        self.set_display_name(display_name)
        self.is_deleted = is_deleted

        self._nickname = None

    def set_username(self, username: str):
        if not 3 <= len(username) <= 30:
            raise ValueError("Username must be between 3 and 30 characters")
        if USERNAME_PATTERN.fullmatch(username) is None:
            raise ValueError(
                "Username must only consist of letters, numbers, underscore, "
                "or period."
            )
        self.username = username

    def set_display_name(self, display_name: str):
        if not 1 <= len(display_name) <= 100:
            raise ValueError(
                "Display name must be between 1 and 100 characters"
            )
        self.display_name = display_name

    def set_nickname(self, nickname: str):
        """Saves this user's nickname to use in other queries. Does not
        make any database changes.
        """
        self._nickname = nickname

    def to_json(self) -> Dict:
        """Returns a JSON representation of this user."""
        json = {
            "id": self.id,
            "username": self.username,
            "displayName": self.display_name,
        }
        nickname = getattr(self, "_nickname", None)
        if nickname:
            json["nickname"] = nickname
        return json


class Friendship(db.Model):
    """A friendship between two users."""

    __tablename__ = "Friendships"

    user1_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    user2_id = Column(Integer, ForeignKey(User.id), primary_key=True)

    user1 = db.relationship("User", foreign_keys=[user1_id])
    user2 = db.relationship("User", foreign_keys=[user2_id])

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

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

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

    user = db.relationship("User", foreign_keys=[user_id])
    friend = db.relationship("User", foreign_keys=[friend_id])

    def __init__(self, user_id: int, friend_id: int, nickname: str):
        if user_id == friend_id:
            raise ValueError("Cannot be friends with yourself")
        self.user_id = user_id
        self.friend_id = friend_id
        self.set_nickname(nickname)

    def set_nickname(self, nickname: str):
        if not 1 <= len(nickname) <= 100:
            raise ValueError("Nickname must be between 1 and 100 characters")
        self.nickname = nickname


class DraftNote(db.Model):
    """A draft note."""

    __tablename__ = "DraftNotes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    # Nullable, since a draft doesn't need a recipient yet
    recipient_id = Column(Integer, ForeignKey(User.id))
    text = Column(String(MAX_NOTE_LENGTH), nullable=False, default="")

    user = db.relationship("User", foreign_keys=[user_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    def __init__(
        self, user_id: int, recipient_id: Optional[int] = None, text: str = ""
    ):
        self.user_id = user_id
        self.set_recipient_id(recipient_id)
        self.set_text(text)

    def set_recipient_id(self, recipient_id: Optional[int] = None):
        # Assumes the user and recipient are friends
        if recipient_id is not None and self.user_id == recipient_id:
            raise ValueError("Cannot send note to yourself")
        self.recipient_id = recipient_id

    def set_text(self, text: str):
        if len(text) > MAX_NOTE_LENGTH:
            raise ValueError("Max note length exceeded")
        self.text = text

    def to_json(self) -> Dict:
        """Returns a JSON representation of this draft note."""
        json = {
            "id": self.id,
            "user": self.user.to_json(),
        }
        if self.recipient_id is None:
            json["recipient"] = None
        else:
            json["recipient"] = self.recipient.to_json()
        json["text"] = self.text
        return json

    def is_ready_to_send(self) -> bool:
        try:
            Note(-1, self.recipient_id, self.text)
        except ValueError:
            return False
        return True


class Note(db.Model):
    """A note."""

    __tablename__ = "Notes"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey(User.id), nullable=False)
    recipient_id = Column(Integer, ForeignKey(User.id), nullable=False)
    text = Column(String(MAX_NOTE_LENGTH), nullable=False, default="")
    time_sent = Column(DateTime(timezone=False), nullable=False)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    def __init__(self, sender_id: int, recipient_id: int, text: str):
        if sender_id == recipient_id:
            raise ValueError("Cannot send note to yourself")
        # Assumes user and recipient are friends
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.set_text(text)
        self.time_sent = datetime.utcnow()

    def set_text(self, text: str):
        if len(text) == 0:
            raise ValueError("Note text cannot be blank")
        if len(text) > MAX_NOTE_LENGTH:
            raise ValueError("Max note length exceeded")
        if text.isspace():
            raise ValueError("Note text cannot be all whitespace")
        self.text = text

    def set_deleted(self, is_deleted: bool):
        """Saves whether the current user has deleted this note. Does
        not make any database changes.
        """
        # pylint: disable=attribute-defined-outside-init
        self._is_deleted = is_deleted

    def is_deleted(self) -> bool:
        """Returns whether the current user has deleted this note. Must
        be manually set. Defaults to False.
        """
        return getattr(self, "_is_deleted", False)

    def set_favorited(self, is_favorite: bool):
        """Saves whether the current user has marked this note as a
        favorite. Does not make any database changes.
        """
        # pylint: disable=attribute-defined-outside-init
        self._is_favorite = is_favorite

    def is_favorite(self) -> bool:
        """Returns whether the current user has marked this note as a
        favorite. Must be manually set. Defaults to False.
        """
        return getattr(self, "_is_favorite", False)

    def to_json(self) -> Dict:
        """Returns a JSON representation of this draft note."""
        json = {
            "id": self.id,
            "sender": self.sender.to_json(),
            "recipient": self.recipient.to_json(),
            "text": self.text,
            "timeSent": self.time_sent.isoformat(),
        }
        if hasattr(self, "_is_deleted"):
            json["is_deleted"] = self.is_deleted()
        elif hasattr(self, "_is_favorite"):
            json["is_favorite"] = self.is_favorite()
        return json


class FavoriteNote(db.Model):
    """A note that a user has marked as favorite."""

    __tablename__ = "FavoriteNotes"

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    note_id = Column(Integer, ForeignKey(Note.id), primary_key=True)

    user = db.relationship("User")
    note = db.relationship("Note")

    def __init__(self, user_id: int, note_id: int):
        self.user_id = user_id
        self.note_id = note_id


class DeletedNote(db.Model):
    """A note that has been deleted by a user."""

    __tablename__ = "DeletedNotes"

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    note_id = Column(Integer, ForeignKey(Note.id), primary_key=True)

    user = db.relationship("User")
    note = db.relationship("Note")

    def __init__(self, user_id: int, note_id: int):
        self.user_id = user_id
        self.note_id = note_id
