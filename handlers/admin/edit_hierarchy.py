import re
from filters import IsAdmin
from aiogram import types
from create_bot import dp, db
from middleware.antiflood import rate_limit
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from hierarchy import Hierarchy


@dp.message_handler(IsAdmin(), commands=['show_hierarchy'])
@rate_limit(2, 'show_hierarchy')
async def show_hierarchy(message: types.Message):
    res = db.fetchall("SELECT * FROM specialities")
    if not res:
        await message.answer("No hierarchy now.")
        return


@dp.message_handler(commands=['create_hierarchy'])
@rate_limit(3, 'create_hierarchy')
async def create_hierarchy(message: types.Message):
    msg = message.text
    split_msg = msg.split()
    split_len = len(split_msg)
    if split_len not in range(2, 4):
        await message.answer("Incorrect format.")
        return




@dp.inline_handler(Text(startswith=['delete']))
async def delete_speciality(query: types.InlineQuery):
    print(query)

