"""
Helper methods for notes.
"""

# =============================================================================

from typing import Optional

import backend
from backend._utils import query
from backend.models import DraftNote, Note, db

# =============================================================================


def get_draft(draft_id: int) -> Optional[DraftNote]:
    return query(DraftNote, DraftNote.id == draft_id).one_or_none()


def create_draft(
    user_id: int, recipient_id: Optional[int], text: str
) -> DraftNote:
    """Creates a draft note with the given info.

    Errors are raised if the args are invalid in any way.
    """
    draft = DraftNote(user_id, recipient_id, text)

    if recipient_id is not None and not backend.friend.are_friends(
        user_id, recipient_id
    ):
        raise ValueError("Can only send notes to friends")

    db.session.add(draft)
    db.session.commit()
    return draft


def edit_draft(
    draft: DraftNote, recipient_id: Optional[int] = None, text: str = None
) -> DraftNote:
    """Edits the draft with the given info.

    Errors are raised if the args are invalid in any way.
    """
    changed = False

    if recipient_id is not None and recipient_id != draft.recipient_id:
        if not backend.friend.are_friends(draft.user_id, recipient_id):
            raise ValueError("Can only send notes to friends")

        draft.set_recipient_id(recipient_id)
        changed = True

    if text is not None and text != draft.text:
        draft.set_text(text)
        changed = True

    if changed:
        db.session.commit()

    return draft


def delete_draft(draft: DraftNote):
    """Deletes the given draft."""
    db.session.delete(draft)
    db.session.commit()


# =============================================================================


def create(user_id: int, recipient_id: int, text: str) -> Note:
    """Creates a note with the given info.

    Errors are raised if the args are invalid in any way.
    """
    note = Note(user_id, recipient_id, text)

    if not backend.friend.are_friends(user_id, recipient_id):
        raise ValueError("Can only send notes to friends")

    db.session.add(note)
    db.session.commit()
    return note
