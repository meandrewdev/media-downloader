import asyncio

from heartbeat import start_heartbeat
from telegrambot import start_bot


def main():
    tasks = [start_heartbeat(), start_bot()]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))


if __name__ == '__main__':
    main()
