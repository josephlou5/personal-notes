"""
Contains the global Flask app instance (and some server code).
"""

# =============================================================================

from datetime import datetime

import pytz
from flask import Flask, redirect, request, url_for
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


def url_template_for(endpoint, **kwargs):
    """Returns a url for the given endpoint with the arguments replaced."""
    url = url_for(
        endpoint, **{key: value for key, (value, _) in kwargs.items()}
    )
    for _, (value, template) in kwargs.items():
        url = url.replace(str(value), str(template))
    return url


def dt_localize(naive_dt: datetime):
    """Localizes a naive datetime object to UTC."""
    return pytz.utc.localize(naive_dt)


@app.context_processor
def inject_template_variables():
    variables = {
        "APP_NAME": APP_NAME,
        "REPO_URL": "https://github.com/josephlou5/personal-notes",
        "url_template_for": url_template_for,
        "dt_localize": dt_localize,
    }
    session_user = get_logged_in_user()
    variables.update(
        {
            "user_is_logged_in": session_user is not None,
            "logged_in_user": session_user,
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
