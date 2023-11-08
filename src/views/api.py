"""
API methods.
"""

# =============================================================================

from functools import wraps

from flask import request

import backend
from utils.auth import get_logged_in_user
from utils.server import AppRoutes

# =============================================================================

app = AppRoutes()

# =============================================================================


def api_route(rule, **options):
    """A decorator that returns an unsuccessful API result if a user is
    not logged in.
    """

    def decorator(func):
        @app.route(rule, **options)
        @wraps(func)
        def wrapper(*args, **kwargs):
            session_user = get_logged_in_user()
            if session_user is None:
                # No one is logged in
                return {"success": False, "error": "User is not logged in"}
            return func(session_user, *args, **kwargs)

        return wrapper

    return decorator


# =============================================================================


@api_route("/api/friends/", methods=["GET"])
def list_user_friends(session_user):
    friends = backend.friend.get_friend_usernames(session_user["id"])
    return {"success": True, "usernames": friends}


@api_route("/api/friends/<int:user_id>/", methods=["POST", "DELETE"])
def update_friendship(session_user, user_id):
    session_user_id = session_user["id"]

    user = backend.user.get(user_id)
    if user is None:
        return {"success": False, "error": "Requested user does not exist"}

    if request.method == "POST":
        # Accept friend request from `user_id`
        try:
            backend.friend.accept_request(user_id, session_user_id)
        except ValueError as ex:
            return {"success": False, "error": str(ex)}
        return {"success": True}

    elif request.method == "DELETE":
        # Remove friend
        try:
            backend.friend.remove(user_id, session_user_id)
        except ValueError as ex:
            return {"success": False, "error": str(ex)}
        return {"success": True}

    return {"success": False, "error": f"Unsupported method: {request.method}"}


@api_route("/api/friends/<int:user_id>/nickname", methods=["POST"])
def update_friend_nickname(session_user, user_id):
    session_user_id = session_user["id"]

    user = backend.user.get(user_id)
    if user is None:
        return {"success": False, "error": "Requested user does not exist"}

    # Get request args
    args = request.get_json(silent=True)
    if args is None:
        return {"success": False, "error": "Invalid JSON data"}
    nickname = args.get("nickname")
    if nickname is None:
        return {
            "success": False,
            "error": "Invalid JSON data: missing 'nickname' key",
        }
    nickname = str(nickname).strip()

    try:
        backend.friend.set_nickname(session_user_id, user_id, nickname)
    except ValueError as ex:
        return {"success": False, "error": str(ex)}
    return {"success": True}


# =============================================================================


@api_route("/api/friend_requests/outgoing", methods=["GET"])
def list_user_outgoing_friend_requests(session_user):
    usernames = backend.friend.get_outgoing_friend_requests(session_user["id"])
    return {"success": True, "usernames": usernames}


@api_route("/api/friend_requests/incoming", methods=["GET"])
def list_user_incoming_friend_requests(session_user):
    usernames = backend.friend.get_incoming_friend_requests(session_user["id"])
    return {"success": True, "usernames": usernames}


@api_route("/api/friend_requests/<int:user_id>", methods=["POST", "DELETE"])
def update_friend_request(session_user, user_id):
    session_user_id = session_user["id"]

    user = backend.user.get(user_id)
    if user is None:
        return {"success": False, "error": "Requested user does not exist"}

    if request.method == "POST":
        # Send friend request to `user_id`
        try:
            backend.friend.send_request(session_user_id, user_id)
        except ValueError as ex:
            return {"success": False, "error": str(ex)}
        return {"success": True}

    elif request.method == "DELETE":
        # Cancel friend request
        try:
            backend.friend.cancel_request(session_user_id, user_id)
        except ValueError as ex:
            return {"success": False, "error": str(ex)}
        return {"success": True}

    return {"success": False, "error": f"Unsupported method: {request.method}"}
