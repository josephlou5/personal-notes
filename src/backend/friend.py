"""
Helper methods for friendships, friend requests, and friend nicknames.
"""

# =============================================================================

from typing import List, Optional

from sqlalchemy import and_, select

from backend._utils import query
from backend.models import FriendNickname, FriendRequest, Friendship, User, db

# =============================================================================


def get_all(user_id: int) -> List[User]:
    """Returns the requested user's friends.

    The users will be sorted by username alphabetically.
    """
    # Split into two queries because otherwise `User` instances will not
    # be returned
    users_with_nicknames = (
        db.session.execute(
            select(User, FriendNickname.nickname)
            .select_from(Friendship)
            .join(User, User.id == Friendship.user2_id)
            .outerjoin(
                FriendNickname,
                and_(
                    FriendNickname.user_id == user_id,
                    FriendNickname.friend_id == User.id,
                ),
            )
            .where(Friendship.user1_id == user_id)
        ).all()
        + db.session.execute(
            select(User, FriendNickname.nickname)
            .select_from(Friendship)
            .join(User, User.id == Friendship.user1_id)
            .outerjoin(
                FriendNickname,
                and_(
                    FriendNickname.user_id == user_id,
                    FriendNickname.friend_id == User.id,
                ),
            )
            .where(Friendship.user2_id == user_id)
        ).all()
    )
    users = []
    for user, nickname in users_with_nicknames:
        if nickname:
            user.set_nickname(nickname)
        users.append(user)
    return sorted(users, key=lambda u: u.username)


def _get_friendship(user1_id: int, user2_id: int) -> Optional[Friendship]:
    if user1_id > user2_id:
        user1_id, user2_id = user2_id, user1_id
    return query(
        Friendship,
        and_(Friendship.user1_id == user1_id, Friendship.user2_id == user2_id),
    ).one_or_none()


def are_friends(user1_id: int, user2_id: int) -> bool:
    """Returns whether the two given users are friends."""
    if user1_id == user2_id:
        # Can't be friends with yourself
        return False

    return _get_friendship(user1_id, user2_id) is not None


def remove(user1_id: int, user2_id: int):
    """Removes a friendship between the two given users."""
    if user1_id == user2_id:
        raise ValueError("Cannot be friends with yourself")

    friendship = _get_friendship(user1_id, user2_id)
    if friendship is None:
        raise ValueError("Users are not friends")

    db.session.delete(friendship)
    db.session.commit()


# =============================================================================


def get_outgoing_friend_requests(user_id: int) -> List[User]:
    """Returns the recipients of the user's outgoing friend requests.

    The users will be sorted by username alphabetically.
    """
    return sorted(
        (
            request.recipient
            for request in query(
                FriendRequest, FriendRequest.sender_id == user_id
            ).all()
        ),
        key=lambda u: u.username,
    )


def get_incoming_friend_requests(user_id: int) -> List[User]:
    """Returns the senders of the user's incoming friend requests.

    The users will be sorted by username alphabetically.
    """
    return sorted(
        (
            request.sender
            for request in query(
                FriendRequest, FriendRequest.recipient_id == user_id
            ).all()
        ),
        key=lambda u: u.username,
    )


# =============================================================================


def _get_friend_request(
    sender_id: int, recipient_id: int
) -> Optional[FriendRequest]:
    return query(
        FriendRequest,
        and_(
            FriendRequest.sender_id == sender_id,
            FriendRequest.recipient_id == recipient_id,
        ),
    ).one_or_none()


def has_sent_request(sender_id: int, recipient_id: int) -> bool:
    """Returns whether the sender has sent a friend request to the
    recipient.
    """
    return _get_friend_request(sender_id, recipient_id) is not None


def send_request(sender_id: int, recipient_id: int):
    """Sends a friend request from the sender to the recipient."""
    if are_friends(sender_id, recipient_id):
        raise ValueError("Already friends")
    if has_sent_request(sender_id, recipient_id):
        raise ValueError("Friend request has already been sent")

    db.session.add(FriendRequest(sender_id, recipient_id))
    db.session.commit()


def cancel_request(sender_id: int, recipient_id: int):
    """Cancels a friend request from the sender to the recipient."""
    friend_request = _get_friend_request(sender_id, recipient_id)
    if friend_request is None:
        raise ValueError("Friend request does not exist")

    db.session.delete(friend_request)
    db.session.commit()


def reject_request(recipient_id: int, sender_id: int):
    """Rejects a friend request from the sender to the recipient."""
    friend_request = _get_friend_request(sender_id, recipient_id)
    if friend_request is None:
        raise ValueError("Friend request does not exist")

    db.session.delete(friend_request)
    db.session.commit()


def accept_request(sender_id: int, recipient_id: int):
    """Accepts a friend request from the sender to the recipient.

    Should be called when the recipient takes an action to accept a
    friend request from the sender.
    """
    friend_request = _get_friend_request(sender_id, recipient_id)
    if friend_request is None:
        raise ValueError("Friend request does not exist")

    db.session.add(Friendship(sender_id, recipient_id))
    db.session.delete(friend_request)
    db.session.commit()


# =============================================================================


def _get_nickname(user_id: int, friend_id: int) -> Optional[FriendNickname]:
    return query(
        FriendNickname,
        and_(
            FriendNickname.user_id == user_id,
            FriendNickname.friend_id == friend_id,
        ),
    ).one_or_none()


def get_nickname(user_id: int, friend_id: int) -> str:
    """Returns the nickname that the user has given their friend.

    Returns the empty string if no nickname has been given.
    """
    nickname = _get_nickname(user_id, friend_id)
    if nickname is None:
        return ""
    return nickname.nickname


def set_nickname(user_id: int, friend_id: int, nickname: str):
    """Sets the nickname that the user has given their friend."""
    nickname = nickname.strip()

    nickname_obj = _get_nickname(user_id, friend_id)
    if nickname_obj is None:
        if len(nickname) == 0:
            # No nickname; do nothing
            return
        db.session.add(FriendNickname(user_id, friend_id, nickname))
    elif len(nickname) == 0:
        # Remove the nickname
        db.session.delete(nickname_obj)
    else:
        nickname_obj.set_nickname(nickname)

    db.session.commit()
