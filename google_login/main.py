#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Any, Dict

import jinja2
from aiohttp import web
from aiohttp_jinja2 import setup as jinja2_setup, template
from aiohttp_session import SimpleCookieStorage, get_session, setup as session_setup
from aiohttp_oauth2 import oauth2_app
import jwt


from aiohttp_oauth2.client.contrib import github


@template("index.html")
async def index(request: web.Request) -> Dict[str, Any]:
    session = await get_session(request)
    print(session)
    return {"user": session.get("user")}


async def logout(request: web.Request):
    session = await get_session(request)
    session.invalidate()
    return web.HTTPTemporaryRedirect(location="/")


async def on_google_error(request: web.Request):
    print(request)


async def on_github_login(request: web.Request, github_token):
    session = await get_session(request)
    id_token = github_token.get('id_token')
    print('token: ' + str(github_token))
    print('session: ' + str(session))
    print('access_token: ' + github_token['access_token'])
    async with request.app["session"].get(
            "https://oauth2.googleapis.com/tokeninfo?id_token=" + id_token,
            headers={"Authorization": f"Bearer {github_token['access_token']}"},
    ) as r:
        print('r: ' + str(r))
        user_info = await r.json()
        session["user"] = user_info.get('name')
        # print('body: ' + str(r.body))
    return web.HTTPTemporaryRedirect(location="/")


def app_factory() -> web.Application:
    app = web.Application()

    jinja2_setup(
        app, loader=jinja2.FileSystemLoader([Path(__file__).parent / "templates"])
    )
    session_setup(app, SimpleCookieStorage())
    app.add_subapp(
        "/google/",
        oauth2_app(
            # ...,
            client_id=os.getenv('CLIENT_ID'),
            client_secret=os.getenv('CLIENT_SECRET'),
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://www.googleapis.com/oauth2/v4/token",
            on_login=on_github_login,
            on_error=on_google_error,
            scopes=['email', 'profile', 'openid']
        )
    )

    app.add_routes([web.get("/", index), web.get("/auth/logout", logout)])

    return app


if __name__ == "__main__":
    web.run_app(app_factory(), host="localhost")
