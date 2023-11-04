"""
Utilities for authentication and authorization.
"""

# =============================================================================

import functools
from typing import Optional

from flask import redirect, request, session, url_for
from werkzeug.exceptions import Forbidden

import backend

# =============================================================================

__all__ = (
    "_redirect_last",
    "set_redirect_page",
    "get_email",
    "is_logged_in",
    "is_logged_in_admin",
    "login_required",
)

# =============================================================================


def _redirect_last(force_default=False):
    """Redirects to the redirect page."""
    default_uri = url_for("index")
    if force_default:
        redirect_uri = default_uri
    else:
        redirect_uri = session.get("redirect_page", default_uri)
    return redirect(redirect_uri)


def set_redirect_page():
    """Sets the current page as the page to redirect to."""
    session["redirect_page"] = request.path


# =============================================================================


def get_email() -> Optional[str]:
    """Gets the email of the currently logged in user, or None."""
    return session.get("email", None)


def is_logged_in() -> bool:
    """Returns True if a user is currently logged in."""
    return get_email() is not None


def is_logged_in_admin() -> bool:
    """Returns True if the currently logged in user is an admin.

    If no user is logged in, returns False.
    """
    email = get_email()
    if email is None:
        return False
    return backend.user.is_admin_email(email)


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
                    return _redirect_last(force_default=True)
                raise Forbidden(
                    "You do not have permission to view an admin page."
                )
            return func(*args, **kwargs)

        return wrapper

    return login_wrapper
