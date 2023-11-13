"""
Utilities for authentication and authorization.
"""

# =============================================================================

import functools
from typing import Dict, Optional

from flask import redirect, request, session, url_for
from werkzeug.exceptions import Forbidden

import backend

# =============================================================================

__all__ = (
    "redirect_last",
    "set_redirect_page",
    "set_logged_in_user",
    "get_email",
    "get_logged_in_user",
    "is_logged_in",
    "is_logged_in_admin",
    "login_required",
)

# =============================================================================


def redirect_last(force_default=False):
    """Redirects to the redirect page."""
    default_uri = url_for("notes" if is_logged_in() else "index")
    if force_default:
        redirect_uri = default_uri
    else:
        redirect_uri = session.get("redirect_page", default_uri)
    return redirect(redirect_uri)


def set_redirect_page():
    """Sets the current page as the page to redirect to."""
    session["redirect_page"] = request.path


# =============================================================================


def set_logged_in_user(user: backend.models.User):
    session["user"] = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "is_admin": user.is_admin,
    }


def get_email() -> Optional[str]:
    """Gets the email of the currently logged in user, or None."""
    return session.get("email", None)


def get_logged_in_user() -> Optional[Dict]:
    """Gets the currently logged in user, or None if no one is logged
    in (or the user hasn't been created yet).

    The returned user is a dictionary containing values for a user.
    """
    email = get_email()
    session_user = session.get("user", None)
    if session_user is None or session_user["email"] != email:
        if email is None:
            # No one is logged in
            return None
        user = backend.user.get_by_email(email)
        if user is None:
            # Account not found
            return None
        set_logged_in_user(user)
        session_user = session["user"]
    return session_user


def is_logged_in() -> bool:
    """Returns True if a user is currently logged in."""
    return get_logged_in_user() is not None


def is_logged_in_admin() -> bool:
    """Returns True if the currently logged in user is an admin.

    If no user is logged in, returns False.
    """
    user = get_logged_in_user()
    if user is None:
        return False
    return user["is_admin"]


# =============================================================================


def login_required(admin=False, save_redirect=True):
    """A decorator to protect an endpoint with a login.

    Args:
        admin (bool): Whether the endpoint is only for admins.
        save_redirect (bool): Whether to allow this endpoint to be
            redirected to upon successful login.
    """

    def login_wrapper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            redirected_to_this_page = (
                session.get("redirect_page", None) == request.path
            )
            if save_redirect:
                set_redirect_page()
            if not is_logged_in():
                return redirect(url_for("log_in"))
            # If the user was redirected to a page they don't have
            # permission to view, redirect them elsewhere. However, if
            # they went to this page specifically, show them a forbidden
            # page.
            if admin and not is_logged_in_admin():
                # Not an admin
                if redirected_to_this_page:
                    return redirect_last(force_default=True)
                raise Forbidden(
                    "You do not have permission to view an admin page."
                )
            return func(*args, **kwargs)

        return wrapper

    return login_wrapper
