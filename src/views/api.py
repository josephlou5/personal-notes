"""
API methods.
"""

# =============================================================================

from functools import wraps
from typing import Dict, Optional, Tuple

from flask import render_template, request, url_for

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


@app.route("/api/<path:subpath>", methods=["GET", "POST", "DELETE"])
def unrecognized_api_method(subpath):
    return {
        "success": False,
        "error": f"Invalid API route: {request.method} {request.path}",
    }


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


@api_route("/api/friend_requests/<int:user_id>/reject", methods=["DELETE"])
def reject_friend_request(session_user, user_id):
    session_user_id = session_user["id"]

    user = backend.user.get(user_id)
    if user is None:
        return {"success": False, "error": "Requested user does not exist"}

    try:
        backend.friend.reject_request(session_user_id, user_id)
    except ValueError as ex:
        return {"success": False, "error": str(ex)}
    return {"success": True}


# =============================================================================


@api_route("/api/danger/friends", methods=["DELETE"])
def delete_all_friends(session_user):
    backend.friend.remove_all(session_user["id"])
    return {"success": True}


@api_route("/api/danger/drafts", methods=["DELETE"])
def delete_all_drafts(session_user):
    backend.note.delete_all_drafts(session_user["id"])
    return {"success": True}


@api_route("/api/danger/notes/unsend", methods=["DELETE"])
def unsend_all_notes(session_user):
    backend.note.unsend_all(session_user["id"])
    return {"success": True}


@api_route("/api/danger/notes", methods=["DELETE"])
def delete_all_received_notes(session_user):
    backend.note.delete_all_received_notes(session_user["id"])
    return {"success": True}


# =============================================================================


@api_route("/api/drafts/", methods=["GET"])
def list_drafts(session_user):
    session_user_id = session_user["id"]

    as_html = "html" in request.args

    drafts = backend.note.get_all_drafts(session_user_id)

    if as_html:
        return {
            "success": True,
            "numNotes": len(drafts),
            "notesHtml": render_template(
                "notes/notes_list.jinja",
                are_deleted=False,
                are_drafts=True,
                notes=drafts,
            ),
        }

    return {
        "success": True,
        "notes": [draft.to_json() for draft in drafts],
    }


def _get_draft_args(
    args: Dict, recipient_required: bool = False, text_required: bool = True
) -> Tuple[Optional[int], Optional[str]]:
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
    if text_required and text is None:
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


@api_route("/api/drafts/send", methods=["POST"])
def send_draft(session_user):
    session_user_id = session_user["id"]

    # Get request args
    args = request.get_json(silent=True)
    if args is None:
        return {"success": False, "error": "Invalid JSON data"}
    try:
        DRAFT_ID_KEY = "draftId"
        draft_id = args.get(DRAFT_ID_KEY, None)
        if draft_id is not None:
            try:
                draft_id = int(draft_id)
            except ValueError:
                raise ValueError(
                    f"expected int for {DRAFT_ID_KEY!r} key"
                ) from None

        # If draft ID is not given, we need the note parameters
        # Otherwise, get them if they exist (override the saved draft)
        required = draft_id is None
        recipient_id, text = _get_draft_args(
            args, recipient_required=required, text_required=required
        )
    except ValueError as ex:
        return {"success": False, "error": f"Invalid JSON data: {ex}"}

    try:
        draft = None
        if draft_id is not None:
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
            if recipient_id is not None:
                draft.set_recipient_id(recipient_id)
            else:
                recipient_id = draft.recipient_id
            if text is not None:
                draft.set_text(text)
            else:
                text = draft.text

            if not draft.is_ready_to_send():
                return {
                    "success": False,
                    "error": "Draft is not ready to send",
                }

        note = backend.note.create(session_user_id, recipient_id, text)

        if draft is not None:
            # Delete the draft
            backend.note.delete_draft(draft)
    except ValueError as ex:
        return {"success": False, "error": str(ex)}

    return {"success": True, "noteId": note.id}


# =============================================================================


@api_route("/api/notes/", methods=["GET"])
def list_notes(session_user):
    session_user_id = session_user["id"]

    as_html = "html" in request.args

    notes = backend.note.get_all(session_user_id)

    if as_html:
        return {
            "success": True,
            "numNotes": len(notes),
            "notesHtml": render_template(
                "notes/notes_list.jinja",
                are_deleted=False,
                are_drafts=False,
                notes=notes,
            ),
        }

    return {
        "success": True,
        "notes": [note.to_json() for note in notes],
    }


@api_route("/api/notes/deleted", methods=["GET"])
def list_deleted_notes(session_user):
    session_user_id = session_user["id"]

    as_html = "html" in request.args

    notes = backend.note.get_deleted(session_user_id)

    if as_html:
        return {
            "success": True,
            "numNotes": len(notes),
            "notesHtml": render_template(
                "notes/notes_list.jinja",
                are_deleted=True,
                are_drafts=False,
                notes=notes,
            ),
        }

    return {
        "success": True,
        "notes": [note.to_json() for note in notes],
    }


@api_route("/api/notes/favorites", methods=["POST"])
def toggle_favorite(session_user):
    # Note: This URL is hard-coded in `notes.js` since templating is not
    # available there

    NOTE_ID_KEY = "noteId"

    session_user_id = session_user["id"]

    args = request.get_json(silent=True)
    if args is None:
        return {"success": False, "error": "Invalid JSON data"}
    try:
        note_id = args.get(NOTE_ID_KEY, None)
        if note_id is None:
            raise ValueError(f"missing {NOTE_ID_KEY!r} key")
        try:
            note_id = int(note_id)
        except ValueError:
            raise ValueError(f"expected int for {NOTE_ID_KEY!r} key") from None
    except ValueError as ex:
        return {"success": False, "error": f"Invalid JSON data: {ex}"}

    note = backend.note.get(note_id)
    if note is None:
        return {
            "success": False,
            "error": f"Note not found with ID: {note_id}",
        }

    is_favorite = backend.note.toggle_favorite(session_user_id, note.id)
    return {"success": True, "isFavorite": is_favorite}


@api_route("/api/notes/<int:note_id>/delete", methods=["POST", "DELETE"])
def delete_note(session_user, note_id):
    """Deletes or undeletes the given note for the requesting user only.

    POST will undelete the note, while DELETE will delete it.
    """
    session_user_id = session_user["id"]

    note = backend.note.get(note_id)
    if note is None:
        return {
            "success": False,
            "error": f"Note not found with ID: {note_id}",
        }

    if request.method == "POST":
        backend.note.undelete_for_user(note, session_user_id)
        return {"success": True}
    elif request.method == "DELETE":
        backend.note.delete_for_user(note, session_user_id)
        return {"success": True}

    return {"success": False, "error": f"Unsupported method: {request.method}"}


@api_route("/api/notes/<int:note_id>/unsend", methods=["DELETE"])
def unsend_note(session_user, note_id):
    """Unsends the note (deletes for everyone)."""
    session_user_id = session_user["id"]

    note = backend.note.get(note_id)
    if note is None:
        return {
            "success": False,
            "error": f"Note not found with ID: {note_id}",
        }
    if note.sender_id != session_user_id:
        return {
            "success": False,
            "error": "Note does not belong to requesting user",
        }

    backend.note.unsend(note)
    return {"success": True}
