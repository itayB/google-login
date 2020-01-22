import base64
import cryptography
import jinja2
import logging
import os
from pathlib import Path
from aiohttp import web
from aiohttp_jinja2 import setup as jinja2_setup
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from oauth2 import oauth2_app, index, logout, on_google_error, on_google_login

from google_login.handlers.status_handler import StatusView

logger = logging.getLogger()


def app_factory(client_id: str, client_secret: str) -> web.Application:
    fernet_key = cryptography.fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    app = web.Application()
    # session_setup(app, SimpleCookieStorage())  # used for testing purpose
    session_setup(app, EncryptedCookieStorage(secret_key))
    jinja2_setup(
        app, loader=jinja2.FileSystemLoader([Path(__file__).parent / "templates"])
    )

    app.add_subapp(
        "/google/",
        oauth2_app(
            # ...,
            client_id=client_id,
            client_secret=client_secret,
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://www.googleapis.com/oauth2/v4/token",
            on_login=on_google_login,
            on_error=on_google_error,
            scopes=['email', 'profile', 'openid']
        )
    )

    app.add_routes([web.get("/", index), web.get("/auth/logout", logout)])
    return app


if __name__ == "__main__":
    client_id = os.getenv('CLIENT_ID')
    if not client_id:
        logger.warning('CLIENT_ID environment variable is missing')
        exit(1)
    client_secret = os.getenv('CLIENT_SECRET')
    if not client_secret:
        logger.warning('CLIENT_SECRET environment variable is missing')
        exit(1)
    app = app_factory(client_id, client_secret)
    app.add_routes([
        web.view('/status', StatusView)
    ])
    web.run_app(app, host="0.0.0.0", port=80)
