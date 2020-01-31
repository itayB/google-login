import logging
from aiohttp import web
from aiohttp.abc import Request
from prometheus_client import Summary

logger = logging.getLogger()

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')


class StatusView(web.View):
    def __init__(self, request: Request) -> None:
        """
        This constructor is being fired per request
        :param request:
        """
        super().__init__(request)

    # Decorate function with metric.
    @REQUEST_TIME.time()
    async def get(self):
        app = self.request.app
        response = {
            'name': 'python-app',
            'version': app.get('version'),
            'uptime': app.get('uptime'),
        }
        return web.json_response(response)
