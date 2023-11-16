"""
Views for notes.
"""

# =============================================================================

from werkzeug.exceptions import NotFound

import backend
from utils.auth import get_logged_in_user, login_required
from utils.server import AppRoutes, _render

# =============================================================================

app = AppRoutes()

# =============================================================================


@app.route("/notes/", methods=["GET"])
@login_required()
def notes():
    return _render("notes/index.jinja", include_markdown=True)


@app.route("/notes/deleted", methods=["GET"])
@login_required()
def deleted_notes():
    return _render("notes/deleted.jinja", include_markdown=True)


@app.route("/notes/new", methods=["GET", "POST"])
@login_required()
def create_note():
    return _render("notes/edit_note.jinja", include_markdown=True, draft=None)


@app.route("/drafts/<int:draft_id>/edit", methods=["GET", "POST"])
@login_required()
def edit_draft_note(draft_id):
    draft = backend.note.get_draft(draft_id)
    if draft is None:
        raise NotFound()

    session_user = get_logged_in_user()
    if draft.user_id != session_user["id"]:
        # No permission
        raise NotFound()

    return _render("notes/edit_note.jinja", include_markdown=True, draft=draft)
