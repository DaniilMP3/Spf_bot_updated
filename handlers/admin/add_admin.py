import sqlite3

from filters import IsSuperUser
from aiogram import types
from create_bot import dp
from middleware.antiflood import rate_limit
from utils import db
import logging
from utils.functions import pre_process_string


logger = logging.getLogger(__name__)


@dp.message_handler(IsSuperUser(), commands=['add_admin'], chat_type=types.ChatType.PRIVATE)
@rate_limit(3)
async def add_admin(message: types.Message):
    msg = await pre_process_string(message)
    msg_split = [w.strip() for w in msg.split(',')]

    if len(msg_split) != 1:
        await message.answer("Incorrect format")
        return
    try:
        new_admin_id = msg_split[0]
        if not new_admin_id.isdigit():
            await message.answer("Telegram ID must be a number")
            return
        db.query("INSERT INTO admins VALUES(?, ?, ?)", (None, new_admin_id, 0))
        await message.answer("Admin was added successfully!")

        logger.info(f"Admin {new_admin_id} was added by admin {message.from_user.full_name}")
    except sqlite3.IntegrityError:
        await message.answer("Already in database.")
    except:
        await message.answer("Unexpected error. Contact admin")
        logger.exception("Unexpected error in add_admin handler")


@dp.message_handler(IsSuperUser(), commands=['promote_admin'], chat_type=types.ChatType.PRIVATE)
@dp.message_handler(IsSuperUser(), commands=['demote_admin'], chat_type=types.ChatType.PRIVATE)
@rate_limit(3)
async def promote_admin(message: types.Message):
    msg = await pre_process_string(message)
    msg_split = [w.strip() for w in msg.split(',')]
    if len(msg_split) != 1:
        await message.answer("Incorrect format")
        return
    try:
        admin_to_promote_id = msg_split[0]
        if not admin_to_promote_id.isdigit():
            await message.answer('Telegram ID must be a number')
            return

        if not db.in_database("admins", "telegram_id", admin_to_promote_id):
            await message.answer("This admin is not in database")
            return

        promote = 1  # 1 - promote, 0 - demote
        if message.get_command() == '/demote_admin':
            promote = 0

        if int(admin_to_promote_id) == message.from_user.id:
            await message.answer("You cannot promote or demote yourself.")
            return

        db.query("UPDATE admins SET is_super_user = ? WHERE telegram_id = ?", (promote, admin_to_promote_id,))
        if promote:
            logger.info(f"Superuser {message.from_user.full_name} promotes admin with id {admin_to_promote_id} to superuser")
            await message.answer("Successfully promoted.")
        else:
            logger.info(f"Superuser {message.from_user.full_name} demotes admin with id {admin_to_promote_id} to admin")
            await message.answer("Successfully demoted.")
    except:
        await message.answer("Unexpected error. Contact admin")
        logger.exception("Unexpected error in change_admin_status handler")
