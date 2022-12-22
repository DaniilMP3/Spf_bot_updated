from filters import IsAdmin
from aiogram import types
from create_bot import dp, db
from middleware.antiflood import rate_limit
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from states import EditHierarchy


@dp.message_handler(IsAdmin(), commands=['edit_hierarchy'])
@rate_limit(2, 'edit_hierarchy')
async def show_specialities(message: types.Message):
    specialities = await db.fetchall("SELECT * FROM specialities")

    if not specialities:
        await message.answer("There's no specialities. Enter the new speciality:")
        return

    for s in specialities:
        await message.answer(s.speciality, reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Delete", callback_data=f"delete_{s.id}"),
            types.InlineKeyboardButton("Edit", callback_data=f"edit_{s.id}"),
            types.InlineKeyboardButton("Next step", callback_data=f"nextstep_{s.id}")
        ))


@dp.inline_handler(Text(startswith=['delete']))
async def delete_speciality(query: types.InlineQuery):
    print(query)