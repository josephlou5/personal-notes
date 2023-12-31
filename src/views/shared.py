"""
Shared global views.
"""

# =============================================================================

from utils import changelog
from utils.auth import set_redirect_page
from utils.server import AppRoutes, _render

# =============================================================================

app = AppRoutes()

# =============================================================================


@app.route("/", methods=["GET"])
def index():
    set_redirect_page()
    latest_version = changelog.get_latest_version()
    return _render("index.jinja", version=latest_version)


# =============================================================================


@app.route("/changelog", methods=["GET"])
def view_changelog():
    set_redirect_page()
    changes = changelog.read_changelog()
    return _render("changelog.jinja", changes=changes)
