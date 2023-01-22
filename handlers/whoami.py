from aiogram import types
from filters import *
from create_bot import dp, meetings_manager
from middleware.antiflood import rate_limit
from db_instance import db


@dp.message_handler(IsRegistered(), commands=['whoami'], chat_type=types.ChatType.PRIVATE)
@rate_limit(3, 'whoami')
async def registered_whoami(message: types.Message):
    user_id = message.from_user.id
    user_data = meetings_manager.get_userInfo(user_id)

    meetings_count = db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))[6]

    user_sex, user_course, user_speciality, user_group = user_data[0], user_data[1], user_data[2], user_data[3]
    await message.answer("STATUS: REGISTERED\n"
                         f"ACTIVITY: {meetings_count}\n"
                         f"TELEGRAM_ID: {user_id}\n"
                         f"SEX: {user_sex}\n"
                         f"COURSE: {user_course}\n"
                         f"SPECIALITY: {user_speciality}\n"
                         f"GROUP: {user_group},")


@dp.message_handler(IsAdmin(), commands=['whoami'], chat_type=types.ChatType.PRIVATE)
@rate_limit(3, 'whoami')
async def admin_whoami(message: types.Message):
    user_id = message.from_user.id
    await message.answer("STATUS: ADMIN\n"
                         f"TELEGRAM_ID: {user_id}")


@dp.message_handler(IsNotRegistered(), commands=['whoami'], chat_type=types.ChatType.PRIVATE)
@rate_limit(3, 'whoami')
async def notRegistered_whoami(message: types.Message):
    user_id = message.from_user.id
    await message.answer("STATUS: NOT REGISTERED\n"
                         f"TELEGRAM_ID: {user_id}")
