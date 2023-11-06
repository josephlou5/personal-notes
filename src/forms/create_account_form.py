"""
The form to create an account.
"""

# =============================================================================

from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, Regexp

import backend
from forms.wtforms_bootstrap import StringField, SubmitField

# =============================================================================


class CreateAccountForm(FlaskForm):
    """A form to create an account."""

    username = StringField(
        "Username",
        [
            InputRequired("Please enter a username."),
            Length(
                3,
                30,
                "Username must be between %(min)d and %(max)d characters.",
            ),
            Regexp(
                backend.models.USERNAME_PATTERN,
                message=(
                    "Username must only consist of letters, numbers, "
                    "underscore, or period."
                ),
            ),
        ],
    )
    name = StringField(
        "Name",
        [
            InputRequired("Please enter your name."),
            Length(1, 100, "Name must be less than %(max)d characters."),
        ],
    )

    submit = SubmitField("Create")
