"""
Views for users.
"""

# =============================================================================

from flask import flash, redirect, url_for

import backend
from forms.create_account_form import CreateAccountForm
from utils.auth import get_email, redirect_last, set_logged_in_user
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

    form = CreateAccountForm()

    if form.validate_on_submit():
        try:
            user = backend.user.create(
                email, form.data["username"], form.data["name"]
            )
        except ValueError as ex:
            flash(str(ex))
        else:
            # Save logged in user in session
            set_logged_in_user(user)
            return redirect_last()

    return _render("user/create_account.jinja", form=form)
