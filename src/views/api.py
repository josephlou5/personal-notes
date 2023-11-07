"""
API methods.
"""

# =============================================================================

import backend
from utils.auth import get_logged_in_user
from utils.server import AppRoutes

# =============================================================================

app = AppRoutes()

# =============================================================================


@app.route("/api/friends")
def list_user_friends():
    session_user = get_logged_in_user()
    if session_user is None:
        # No one is logged in
        return {"success": False, "error": "User is not logged in"}
    friends = backend.user.get_friend_usernames(session_user["id"])
    return {"success": True, "friends": friends}
