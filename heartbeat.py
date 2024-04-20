from aiohttp import web

routes = web.RouteTableDef()


@routes.get('/heartbeat')
async def heartbeat(request):
    return web.Response(text='Heartbeat OK')


async def start_heartbeat():
    app = web.Application()
    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
