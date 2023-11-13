"""
API methods.
"""

# =============================================================================

from functools import wraps
from typing import Dict

from flask import request, url_for

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
    users = backend.friend.get_all(session_user["id"])
    return {"success": True, "users": [user.to_json() for user in users]}


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
    users = backend.friend.get_outgoing_friend_requests(session_user["id"])
    return {"success": True, "users": [user.to_json() for user in users]}


@api_route("/api/friend_requests/incoming", methods=["GET"])
def list_user_incoming_friend_requests(session_user):
    users = backend.friend.get_incoming_friend_requests(session_user["id"])
    return {"success": True, "users": [user.to_json() for user in users]}


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


# =============================================================================


def _get_draft_args(args: Dict, recipient_required=False):
    """Gets and validates args for a draft note.

    Errors should be handled by the caller.
    """
    RECIPIENT_ID_KEY = "recipientId"
    TEXT_KEY = "text"

    recipient_id = args.get(RECIPIENT_ID_KEY, None)
    if recipient_id is None:
        if recipient_required:
            raise ValueError(f"missing {RECIPIENT_ID_KEY!r} key")
    else:
        try:
            recipient_id = int(recipient_id)
        except ValueError:
            raise ValueError(
                f"expected int for {RECIPIENT_ID_KEY!r} key"
            ) from None
    text = args.get(TEXT_KEY, None)
    if text is None:
        raise ValueError(f"missing {TEXT_KEY!r} key")

    return recipient_id, text


@api_route("/api/drafts/", methods=["POST"])
def create_draft_note(session_user):
    session_user_id = session_user["id"]

    # Get request args
    args = request.get_json(silent=True)
    if args is None:
        return {"success": False, "error": "Invalid JSON data"}
    try:
        recipient_id, text = _get_draft_args(args)
    except ValueError as ex:
        return {"success": False, "error": f"Invalid JSON data: {ex}"}

    try:
        draft = backend.note.create_draft(session_user_id, recipient_id, text)
    except ValueError as ex:
        return {"success": False, "error": str(ex)}

    return {
        "success": True,
        "draftId": draft.id,
        "redirectUri": url_for("edit_draft_note", draft_id=draft.id),
    }


@api_route("/api/drafts/<int:draft_id>", methods=["POST", "DELETE"])
def update_draft_note(session_user, draft_id):
    session_user_id = session_user["id"]

    draft = backend.note.get_draft(draft_id)
    if draft is None:
        return {
            "success": False,
            "error": f"Draft not found with ID: {draft_id}",
        }
    if draft.user_id != session_user_id:
        return {
            "success": False,
            "error": "Draft does not belong to requesting user",
        }

    if request.method == "POST":
        # Update draft
        # Get request args
        args = request.get_json(silent=True)
        if args is None:
            return {"success": False, "error": "Invalid JSON data"}
        try:
            recipient_id, text = _get_draft_args(args)
        except ValueError as ex:
            return {"success": False, "error": f"Invalid JSON data: {ex}"}

        backend.note.edit_draft(draft, recipient_id, text)
        return {"success": True}

    elif request.method == "DELETE":
        # Delete draft
        backend.note.delete_draft(draft)
        return {"success": True}

    return {"success": False, "error": f"Unsupported method: {request.method}"}


@api_route("/api/notes/send", methods=["POST"])
def send_note(session_user):
    session_user_id = session_user["id"]

    # Get request args
    args = request.get_json(silent=True)
    if args is None:
        return {"success": False, "error": "Invalid JSON data"}
    try:
        recipient_id, text = _get_draft_args(args, recipient_required=True)

        DRAFT_ID_KEY = "draftId"
        draft_id = args.get(DRAFT_ID_KEY, None)
        if draft_id is not None:
            try:
                draft_id = int(draft_id)
            except ValueError:
                raise ValueError(
                    f"expected int for {DRAFT_ID_KEY!r} key"
                ) from None
    except ValueError as ex:
        return {"success": False, "error": f"Invalid JSON data: {ex}"}

    try:
        note = backend.note.create(session_user_id, recipient_id, text)
    except ValueError as ex:
        return {"success": False, "error": str(ex)}

    if draft_id is not None:
        # Delete the existing draft if the note was created successfully
        draft = backend.note.get_draft(draft_id)
        if draft is not None and draft.user_id == session_user_id:
            # Only delete if exists and has permission; otherwise
            # silently ignore
            backend.note.delete_draft(draft)

    return {"success": True, "noteId": note.id}
