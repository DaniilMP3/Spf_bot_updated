from aiogram import executor, types
from create_bot import dp
from handlers import *
from middleware import ThrottlingMiddleware


@dp.message_handler(commands=['start'], state=None)
async def start(message: types.Message):
    await message.answer("Start. If you are not registered yet, enter /registration.")


async def on_startup(_):
    db.create_tables()
    dp.setup_middleware(ThrottlingMiddleware())
    print("Online")


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
