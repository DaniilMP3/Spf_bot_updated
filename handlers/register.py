import re
from aiogram import types
from create_bot import dp, db
from aiogram.dispatcher.filters import Text
from middleware.antiflood import rate_limit
from filters import IsRegistered
from states import Register
from aiogram.dispatcher import FSMContext


@dp.message_handler(not IsRegistered(), commands=["register"], state=None)
@rate_limit(5, "register")
async def start_registration(message: types.Message):
    await message.answer("Start registration. Enter your full name: ")
    await Register.first()


@dp.message_handler(state=Register.full_name)
@rate_limit(2)
async def name_field(message: types.Message, state: FSMContext):
    text = re.sub(' +', ' ', message.text)

    if len(text.split()) != 2 or all(x.isalpha() or x.isspace() for x in message.text):
        await message.answer("Incorrect format")
        return

    await state.update_data(full_name=text)
    await Register.next()


@dp.message_handler(state=Register.sex)
@rate_limit(2)
async def sex_field(message: types.Message, state: FSMContext):
    text = message.text
    if text not in ["male", "female"]:
        await message.answer("Incorrect format")
        return

    await state.update_data(sex=text)
    await Register.next()


@dp.message_handler(state=Register.speciality)
@rate_limit(2)
async def speciality_field(message: types.Message, state: FSMContext):
    pass

