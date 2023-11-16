"""
Helper methods for notes.
"""

# =============================================================================

import itertools
from typing import List, Optional

from sqlalchemy import and_, or_, select

import backend
from backend._utils import query
from backend.models import DeletedNote, DraftNote, FavoriteNote, Note, db

# =============================================================================


def get_draft(draft_id: int) -> Optional[DraftNote]:
    return query(DraftNote, DraftNote.id == draft_id).one_or_none()


def get_all_drafts(user_id: int) -> List[DraftNote]:
    return query(DraftNote, DraftNote.user_id == user_id).all()


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


def delete_all_drafts(user_id: int):
    """Deletes all the drafts for the given user."""
    drafts = get_all_drafts(user_id)
    if len(drafts) == 0:
        return
    for draft in drafts:
        db.session.delete(draft)
    db.session.commit()


# =============================================================================


def get(note_id: int) -> Optional[Note]:
    return query(Note, Note.id == note_id).one_or_none()


def get_all(user_id: int) -> List[Note]:
    """Gets all the notes sent by or sent to the given user. The notes
    will include whether they are favorited by the user.

    The notes will be sorted by most recently sent.
    """
    # Include whether the note is favorited by the given user
    notes_with_favorites = db.session.execute(
        select(Note, FavoriteNote, DeletedNote)
        .outerjoin(
            FavoriteNote,
            and_(
                FavoriteNote.user_id == user_id,
                FavoriteNote.note_id == Note.id,
            ),
        )
        .outerjoin(
            DeletedNote,
            and_(
                DeletedNote.user_id == user_id, DeletedNote.note_id == Note.id
            ),
        )
        .where(or_(Note.sender_id == user_id, Note.recipient_id == user_id))
    ).all()
    notes = []
    for note, favorite, deleted in notes_with_favorites:
        if deleted is not None:
            # Don't include deleted notes
            continue
        note.set_favorited(favorite is not None)
        notes.append(note)
    return sorted(notes, key=lambda n: n.time_sent, reverse=True)


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


def toggle_favorite(user_id: int, note_id: int) -> bool:
    """Toggles whether the note is favorited by the given user.

    Returns whether the note is now favorited by the user.
    """
    favorite = query(
        FavoriteNote,
        and_(FavoriteNote.user_id == user_id, FavoriteNote.note_id == note_id),
    ).one_or_none()
    if favorite is None:
        # Add favorite
        db.session.add(FavoriteNote(user_id, note_id))
        db.session.commit()
        return True
    else:
        # Delete favorite
        db.session.delete(favorite)
        db.session.commit()
        return False


def unsend(note: Note):
    """Unsends the given note."""
    # Couldn't really figure out cascading deletes, so manually delete
    # all children
    children = itertools.chain(
        query(FavoriteNote, FavoriteNote.note_id == note.id).all(),
        query(DeletedNote, DeletedNote.note_id == note.id).all(),
    )
    for child in children:
        db.session.delete(child)
    db.session.delete(note)
    db.session.commit()


def unsend_all(user_id: int):
    """Unsends all notes sent by the given user."""
    notes = query(Note, Note.sender_id == user_id).all()
    if len(notes) == 0:
        return
    # Manually delete all children
    note_ids = set(note.id for note in notes)
    children = itertools.chain(
        query(FavoriteNote, FavoriteNote.note_id.in_(note_ids)).all(),
        query(DeletedNote, DeletedNote.note_id.in_(note_ids)).all(),
    )
    for child in children:
        db.session.delete(child)
    for note in notes:
        db.session.delete(note)
    db.session.commit()


# =============================================================================


def get_deleted(user_id: int) -> List[Note]:
    """Returns the notes that the given user has deleted.

    The notes are sorted by most recently sent.
    """
    deleted = query(DeletedNote, DeletedNote.user_id == user_id).all()
    notes = []
    for deleted_note in deleted:
        note = deleted_note.note
        note.set_deleted(True)
        notes.append(note)
    return sorted(notes, key=lambda n: n.time_sent, reverse=True)


def delete_for_user(note: Note, user_id: int):
    """Deletes the given note for the requesting user only.

    Operation is idempotent: if the user has already deleted this note,
    this has no effect.
    """
    deleted = query(
        DeletedNote,
        and_(DeletedNote.user_id == user_id, DeletedNote.note_id == note.id),
    ).one_or_none()
    if deleted is not None:
        return
    db.session.add(DeletedNote(user_id, note.id))
    db.session.commit()


def delete_all_received_notes(user_id: int):
    """Deletes all the received notes for the given user only."""
    notes_with_deleted = db.session.execute(
        select(Note, DeletedNote)
        .outerjoin(
            DeletedNote,
            and_(
                DeletedNote.user_id == user_id, DeletedNote.note_id == Note.id
            ),
        )
        .where(Note.recipient_id == user_id)
    ).all()
    created = False
    for note, deleted in notes_with_deleted:
        if deleted is not None:
            # Already deleted
            continue
        created = True
        db.session.add(DeletedNote(user_id, note.id))
    if created:
        db.session.commit()


def undelete_for_user(note: Note, user_id: int):
    """Undeletes the given note for the requesting user only.

    Operation is idempotent: if the user has not deleted this note, this
    has no effect.
    """
    deleted = query(
        DeletedNote,
        and_(DeletedNote.user_id == user_id, DeletedNote.note_id == note.id),
    ).one_or_none()
    if deleted is None:
        return
    db.session.delete(deleted)
    db.session.commit()
