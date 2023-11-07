"""
Views for users.
"""

# =============================================================================

from flask import flash, redirect, url_for

import backend
from forms.profile_form import ProfileForm
from utils.auth import (
    get_email,
    get_logged_in_user,
    login_required,
    redirect_last,
    set_logged_in_user,
    set_redirect_page,
)
from utils.server import AppRoutes, _render

# =============================================================================

app = AppRoutes()

# =============================================================================


@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    email = get_email()
    if email is None:
        # No one is logged in
        return redirect(url_for("index"))
    if get_logged_in_user() is not None:
        # User already has an account
        return redirect(url_for("profile"))

    form = ProfileForm()

    if form.validate_on_submit():
        try:
            user = backend.user.create(
                email, form.data["username"], form.data["display_name"]
            )
        except ValueError as ex:
            flash(str(ex), "danger")
        else:
            # Save logged in user in session
            set_logged_in_user(user)
            return redirect_last()

    return _render("user/create_account.jinja", form=form)


@app.route("/profile", methods=["GET", "POST"])
@login_required()
def profile():
    session_user = get_logged_in_user()
    user = backend.user.get(session_user["id"])

    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        try:
            user = backend.user.edit(
                user, form.data["username"], form.data["display_name"]
            )
        except ValueError as ex:
            flash(str(ex), "danger")
        else:
            set_logged_in_user(user)
            flash("Profile successfully saved!", "success")

    return _render("user/profile.jinja", form=form)


@app.route("/@<username>", methods=["GET"])
def public_profile(username):
    set_redirect_page()

    # TODO
    return f"Public profile for: {username}"
