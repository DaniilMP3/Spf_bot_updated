import re
import asyncio
from aiogram import types, Dispatcher
from create_bot import dp
from aiogram.dispatcher.filters import Text
from middleware.antiflood import rate_limit
from filters import *
from states import Register
from aiogram.dispatcher import FSMContext
from db_instance import db
from keyboards import *


MESSAGES = {"full_name": {"message": "Enter your full name: ", "markup": types.ReplyKeyboardRemove},
            "sex": {"message" : "Enter your sex.", "markup": sex_kb},
            "course": {"message": "Enter your course(1-7).", "markup": empty_kb},
            "speciality": {"message": "Enter your speciality.", "markup": getSpecialitiesKeyboard},
            "group": {"message": "Enter your group.", "markup": getGroupsKeyboard}}


@dp.message_handler(state='*', commands="cancel")
@dp.message_handler(Text(equals=cancel_cross), state="*")
@rate_limit(3)
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        return
    await state.finish()
    await message.answer("Canceled", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state="*", commands="previous")
@dp.message_handler(Text(equals=previous_state), state="*")
@rate_limit(1)
async def previous(message: types.Message, state: FSMContext):
    current_state = await state.get_state() ## <class>:<state_name> ##
    if current_state is None:
        return
    className = current_state.split(':')[0]

    if className != str(Register.__name__):
        return

    await Register.previous()
    current_state = await state.get_state()
    if current_state is None:
        await state.finish()
        await message.answer("Canceled.", reply_markup=types.ReplyKeyboardRemove())
    else:
        state_str = current_state.split(':')[1]
        msg, markup = MESSAGES[state_str]["message"], MESSAGES[state_str]["markup"]
        if not callable(markup):
            await message.answer(msg, reply_markup=markup)
        elif asyncio.iscoroutinefunction(markup):
            await message.answer(msg, reply_markup=await markup())
        else:
            await message.answer(msg, reply_markup=markup())


@dp.message_handler(IsNotRegistered(), commands=["register"], state=None)
@rate_limit(5, "register")
async def start_registration(message: types.Message):
    await message.answer("Start registration. Enter your full name: ")
    await Register.first()


@dp.message_handler(IsRegistered(), commands=["register"], state=None)
@rate_limit(5, "register")
async def registration_invalid(message: types.Message):
    await message.answer("You are already registered.")


@dp.message_handler(IsRegistered(), commands=["edit"], state=None)
@rate_limit(5, "edit")
async def start_edit(message: types.Message):
    await message.answer("Start editing. Enter your full name:")
    await Register.first()


@dp.message_handler(IsNotRegistered(), commands=["edit"], state=None)
@rate_limit(5, "edit")
async def edit_invalid(message: types.Message):
    await message.answer("You are not registered yet.")


@dp.message_handler(state=Register.full_name)
@rate_limit(2)
async def name_field(message: types.Message, state: FSMContext):
    name = re.sub(' +', ' ', message.text)
    if len(name.split()) != 2 or not all(x.isalpha() or x.isspace() for x in message.text):
        await message.answer("Incorrect format")
        return

    await state.update_data(full_name=name)
    await Register.next()
    await message.answer("Enter your sex.", reply_markup=sex_kb)


@dp.message_handler(state=Register.sex)
@rate_limit(2)
async def sex_field(message: types.Message, state: FSMContext):
    sex = message.text.lower()
    if sex not in ["male", "female"]:
        await message.answer("Incorrect format")
        return

    await state.update_data(sex=sex)
    await Register.next()
    await message.answer("Enter your course(1-7).", reply_markup=empty_kb)


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
    await message.answer("Enter your speciality.", reply_markup=await getSpecialitiesKeyboard())


@dp.message_handler(state=Register.speciality)
@rate_limit(2)
async def speciality_field(message: types.Message, state: FSMContext):
    speciality = message.text
    query_res = db.fetchone("SELECT * FROM specialities WHERE speciality = ?", (speciality,))
    if not query_res:
        await message.answer("Not-existent speciality")
        return
    speciality_id = query_res[0]
    await state.update_data(speciality_id=speciality_id)
    await Register.next()
    await message.answer("Enter your group.", reply_markup=await getGroupsKeyboard(speciality_id))


@dp.message_handler(state=Register.group)
@rate_limit(2)
async def group_field(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    group = message.text
    async with state.proxy() as data:
        speciality_id = data['speciality_id']

    query_res = db.fetchone("SELECT * FROM users_groups WHERE user_group = ? AND parent_speciality = ?", (group, speciality_id,))
    if not query_res:
        await message.answer("Not-existent group for this speciality.")
        return

    group_id = query_res[0]
    async with state.proxy() as data:
        full_name = data['full_name']
        sex = data['sex']
        course = data['course']

    was_registered = db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

    if was_registered:
        pk_id = was_registered[0]
        db.query("UPDATE users SET full_name = ?, sex = ?, course = ?, user_group = ? WHERE id = ?", (full_name, sex, course, group_id, pk_id))
        await message.answer("Information was changed successfully.", reply_markup=types.ReplyKeyboardRemove())
        return
    else:
        db.query("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?)", (None, user_id, full_name, sex, course, group_id, 0))
        await message.answer("Congrats! Registration completed.", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()

