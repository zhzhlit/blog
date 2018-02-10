import logging
import asyncio

from aiohttp import web

logging.basicConfig(level=logging.INFO)


def index(request):
    return web.Response(body='<h1>Hello!</h1>', content_type='text/html')


# async await  替代 @asyncio.coroutine  yield from
async def init():
    app = web.Application()
    app.router.add_route('GET', '/', index)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)

    logging.info('server start at http://127.0.0.1:9000...')
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init())
loop.run_forever()
