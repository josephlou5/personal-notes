"""
Runs a development server in debug mode.

For HTTPS, you must have a `cert.pem` and `key.pem` file in the root
directory.
"""

# =============================================================================

import os
from pathlib import Path

# =============================================================================

PORT = 5000

ENVIRONMENT_VARIABLES = []

# =============================================================================


def main():
    invalid = False

    for key in ENVIRONMENT_VARIABLES:
        if not os.getenv(key):
            invalid = True
            print("Environment variable not set:", key)

    root = (Path(__file__).parent / "..").resolve()
    for file in ("src/keys.py", "cert.pem", "key.pem"):
        path = (root / file).resolve()
        if not path.exists():
            invalid = True
            print("Missing file:", path.relative_to(root))

    if invalid:
        return

    # Set `FLASK_DEBUG` so that the app is initialized in debug mode
    if not os.getenv("FLASK_DEBUG"):
        # Expects any string
        os.environ["FLASK_DEBUG"] = "True"

    from app import app  # pylint: disable=import-outside-toplevel

    app.run(host="0.0.0.0", port=PORT, ssl_context=("cert.pem", "key.pem"))


if __name__ == "__main__":
    main()
