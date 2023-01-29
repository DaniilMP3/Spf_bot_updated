from aiogram import types
from create_bot import dp
from handlers import *
from middleware import ThrottlingMiddleware
from middleware.antiflood import rate_limit
import asyncio
from aiohttp import web
from api.event_sync.event_sync import event_app, event_routes
from keyboards import cancel_cross
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext


@dp.message_handler(commands=['start'], state=None, chat_type=types.ChatType.PRIVATE)
@rate_limit(3)
async def start(message: types.Message):
    await message.answer("Start. If you are not registered yet, enter /register.")


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

runners = []


async def start_site(application, host, port, routes=None):
    if routes:
        application.add_routes(routes)

    runner = web.AppRunner(application)
    runners.append(runner)

    await runner.setup()
    site = web.TCPSite(runner, host, port)
    print(f"Socket works on {host}:{port}")

    await site.start()


async def on_startup():
    dp.setup_middleware(ThrottlingMiddleware())
    db.create_tables()


async def start_polling():
    print("Bot Online")
    await dp.start_polling()


async def main():
    await asyncio.gather(start_polling(),
                         start_site(event_app, "localhost", 8000, event_routes))


try:
    loop.create_task(on_startup())
    loop.run_until_complete(main())
except:
    pass
finally:
    dp.stop_polling()
    for runner in runners:
        loop.run_until_complete(runner.cleanup())

    print("Shut down. Bye!")




