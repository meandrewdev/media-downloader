from quart import Quart

app = Quart(__name__)


@app.route('/heartbeat')
async def heartbeat():
    return 'Heartbeat OK'


async def start_heartbeat():
    await app.run_task(host='0.0.0.0', port=5000)
