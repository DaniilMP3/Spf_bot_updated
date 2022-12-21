from aiogram import executor
from create_bot import dp, db


async def on_startup(_):
    db.create_tables()
    print("Online")

executor.start_polling(dp, skip_updates=True, on_startup=True)
