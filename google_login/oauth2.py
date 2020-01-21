import logging
from typing import Optional, List, Callable, Dict, Any
from aiohttp import web, ClientSession
from aiohttp_jinja2 import template
from aiohttp_session import get_session
from yarl import URL


logger = logging.getLogger()
routes = web.RouteTableDef()  # pylint: disable=invalid-name


def redirect_uri(request):
    return str(request.url.with_path(str(request.app.router['callback'].url_for())))


@routes.view('/auth', name='auth')
class AuthView(web.View):
    """
    View to kick off the oauth2 flow, this simply redirects the
    client to the oauth2 provider's authorization endpoint
    """

    async def get(self) -> web.Response:
        params = {
            'client_id': self.request.app['CLIENT_ID'],
            'redirect_uri': redirect_uri(self.request),
            'response_type': 'code',
            **self.request.app['AUTH_EXTRAS'],
        }

        if self.request.app['SCOPES']:
            params['scope'] = " ".join(self.request.app['SCOPES'])
        location = str(URL(self.request.app['AUTHORIZE_URL']).with_query(params))
        return web.HTTPTemporaryRedirect(location=location)


@routes.view('/callback', name='callback')
class CallbackView(web.View):
    """
    Handle the oauth2 callback
    """

    async def get(self) -> web.Response:
        if self.request.query.get('error') is not None:
            return await self.handle_error(self.request, self.request.query['error'])

        params = {
            'headers': {
                'Accept': 'application/json'
            }
        }
        body = {
            'client_id': self.request.app['CLIENT_ID'],
            'client_secret': self.request.app['CLIENT_SECRET'],
            'code': self.request.query['code'],
            'redirect_uri': redirect_uri(self.request),
            'grant_type': 'authorization_code',
        }
        if self.request.app['DATA_AS_JSON']:
            params['json'] = body
        else:
            params['data'] = body

        async with self.request.app['session'].post(
                self.request.app['TOKEN_URL'], **params
        ) as r:  # pylint: disable=invalid-name
            result = await r.json()

        return await self.handle_success(self.request, result)

    async def handle_error(self, request: web.Request, error: str):
        handler = request.app.get('ON_ERROR')
        if handler is not None:
            return await handler(request)
        raise web.HTTPInternalServerError(text=f'Unhandled OAuth2 Error: {error}')

    async def handle_success(self, request, user_data):
        handler = request.app.get('ON_LOGIN')
        if handler is not None:
            return await handler(self.request, user_data)
        return web.json_response(user_data)


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


async def client_session(app: web.Application):
    async with ClientSession() as session:
        app["session"] = session
        yield


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


async def on_google_login(request: web.Request, login_data: Dict[str, Any]):
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
