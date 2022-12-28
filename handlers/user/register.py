import re
from aiogram import types, Dispatcher
from create_bot import dp
from aiogram.dispatcher.filters import Text
from middleware.antiflood import rate_limit
from filters import IsNotRegistered
from states import Register
from aiogram.dispatcher import FSMContext
from db_instance import db


@dp.message_handler(IsNotRegistered(), commands=["register"], state=None)
@rate_limit(5, "register")
async def start_registration(message: types.Message):
    await message.answer("Start registration. Enter your full name: ")
    await Register.first()


@dp.message_handler(state=Register.full_name)
@rate_limit(2)
async def name_field(message: types.Message, state: FSMContext):
    name = re.sub(' +', ' ', message.text).lower()
    if len(name.split()) != 2 or not all(x.isalpha() or x.isspace() for x in message.text):
        await message.answer("Incorrect format")
        return

    await state.update_data(full_name=name)
    await Register.next()
    await message.answer("Enter your sex.")


@dp.message_handler(state=Register.sex)
@rate_limit(2)
async def sex_field(message: types.Message, state: FSMContext):
    sex = message.text.lower()
    if sex not in ["male", "female"]:
        await message.answer("Incorrect format")
        return

    await state.update_data(sex=sex)
    await Register.next()
    await message.answer("Enter your course.")


@dp.message_handler(state=Register.course)
@rate_limit(2)
async def course_field(message: types.Message, state: FSMContext):
    msg = message.text
    if not msg.isdigit():
        await message.answer("Enter a number(1-7)")
        return

    elif int(msg) not in range(1, 8):
        await message.answer("Enter a number(1-7)")
        return

    await state.update_data(course=int(msg))
    await Register.next()
    await message.answer("Enter your speciality.")


@dp.message_handler(state=Register.speciality)
@rate_limit(2)
async def speciality_field(message: types.Message, state: FSMContext):
    speciality = message.text.lower()
    query_res = await db.fetchone("SELECT * FROM specialities WHERE speciality = ?", (speciality,))
    if not query_res:
        await message.answer("Not-existent speciality")
        return

    await state.update_data(speciality=query_res.id)
    await Register.next()
    await message.answer("Enter your group.")


@dp.message_handler(state=Register.group)
@rate_limit(2)
async def group_field(message: types.Message, state: FSMContext):
    group = message.text.lower()
    with state.proxy() as data:
        speciality = data['speciality']

    query_res = db.fetchall("SELECT * FROM groups WHERE parent_speciality = ?", (speciality,))
    if not query_res:
        await message.answer("Not-existent group for this speciality.")
        return

    with state.proxy() as data:
        full_name = data['full_name']
        sex = data['sex']
        course = data['course']

    db.query("INSERT INTO users(full_name, sex, course, speciality, user_group, meetings_count)"
             "VALUES(?, ?, ?, ?, ?, ?)", (full_name, sex, course, group, 0))
    await state.finish()
    await message.answer("Congrats! Registration completed.")

