import base64
import cryptography
import jinja2
import logging
import os
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
from aiohttp import ClientSession, web
from aiohttp_jinja2 import setup as jinja2_setup, template
from aiohttp_session import get_session, setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from oauth2 import routes

logger = logging.getLogger()


async def client_session(app: web.Application):
    async with ClientSession() as session:
        app["session"] = session
        yield


def oauth2_app(
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        scopes: Optional[List[str]] = None,
        on_login: Optional[Callable[[web.Request, Dict[str, Any]], web.Response]] = None,
        on_error: Optional[Callable[[web.Request, str], web.Response]] = None,
) -> web.Application:
    auth_app = web.Application()

    auth_app.update(
        CLIENT_ID=client_id,
        CLIENT_SECRET=client_secret,
        AUTHORIZE_URL=authorize_url,
        TOKEN_URL=token_url,
        SCOPES=scopes,
        ON_LOGIN=on_login,
        ON_ERROR=on_error,
        DATA_AS_JSON=True,
        AUTH_EXTRAS={},
    )
    auth_app.cleanup_ctx.append(client_session)
    auth_app.add_routes(routes)
    return auth_app


@template("index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    session = await get_session(request)
    logger.debug(session)
    return {
        'user': session.get('user')
    }


async def logout(request: web.Request):
    session = await get_session(request)
    session.invalidate()
    return web.HTTPTemporaryRedirect(location='/')


async def on_google_error(request: web.Request):
    logger.warning(request)


async def on_google_login(request: web.Request, login_data):
    session = await get_session(request)
    id_token = login_data.get('id_token')
    access_token = login_data.get('access_token')
    logger.debug('token: ' + str(id_token))
    logger.debug('session: ' + str(session))
    logger.debug('access_token: ' + str(access_token))
    async with request.app['session'].get(
            'https://oauth2.googleapis.com/tokeninfo?id_token=' + id_token,
            headers={'Authorization': f'Bearer {access_token}'},
    ) as r:
        user_info = await r.json()
        session['user'] = user_info.get('name')
    return web.HTTPTemporaryRedirect(location="/")


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
    web.run_app(app_factory(client_id, client_secret), host="0.0.0.0", port=80)
