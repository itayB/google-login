import logging
from aiohttp import web
from aiohttp.abc import Request

logger = logging.getLogger()


class StatusView(web.View):
    def __init__(self, request: Request) -> None:
        """
        This constructor is being fired per request
        :param request:
        """
        super().__init__(request)

    async def get(self):
        app = self.request.app
        response = {
            'name': 'python-app',
            'version': app.get('version'),
            'uptime': app.get('uptime'),
        }
        return web.json_response(response)
