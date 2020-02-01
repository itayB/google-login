import time
import logging
from random import randrange

from aiohttp import web
from aiohttp.abc import Request

logger = logging.getLogger()


class Fake1View(web.View):
    def __init__(self, request: Request) -> None:
        """
        This constructor is being fired per request
        :param request:
        """
        super().__init__(request)
        app = request.app
        self.metrics = app.get('metrics')

    async def get(self):
        total = int(self.request.query.get('total', '100'))
        percentage = int(self.request.query.get('percentage', '90'))
        start_time = time.time()
        num = randrange(total)  # Integer from 0 to 9 inclusive
        if num < percentage:
            latency = 0.05  # 50 milliseconds
        else:
            latency = 0.2  # 200 milliseconds
        time.sleep(latency)
        handle_time = time.time() - start_time
        self.metrics.get('request_latency').labels('user1', self.request.path).observe(handle_time)
        return web.json_response({
            'latency': latency,
        })
