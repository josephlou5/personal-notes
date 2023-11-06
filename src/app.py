"""
Contains the global Flask app instance (and some server code).
"""

# =============================================================================

from flask import Flask, redirect, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import NotFound

import backend
import views
from config import get_config
from utils.auth import get_logged_in_user
from utils.server import _render

# =============================================================================

APP_NAME = "Personal Notes"

# =============================================================================

# Set up app

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(get_config(app.debug))

# Set up CSRF protection
CSRFProtect().init_app(app)

# Set up backend database
backend.init_app(app)

# =============================================================================


@app.context_processor
def inject_template_variables():
    variables = {
        "APP_NAME": APP_NAME,
        "REPO_URL": "https://github.com/josephlou5/personal-notes",
    }
    session_user = get_logged_in_user()
    variables.update(
        {
            "user_is_logged_in": session_user is not None,
            "user": session_user,
        }
    )
    return variables


@app.before_request
def before_request():  # pylint: disable=inconsistent-return-statements
    if not request.is_secure:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)


# =============================================================================


def error_view(title, message):
    return _render("error.jinja", title=title, message=message)


@app.errorhandler(404)
@app.errorhandler(405)  # if method is not allowed, also use not found
def error_not_found(e):
    if e.code == 405:
        e = NotFound()
    return error_view("404 Not Found", e.description)


@app.errorhandler(403)
def error_forbidden(e):
    return error_view("Access denied", e.description)


# =============================================================================

# Register all views
views.register_all(app)
