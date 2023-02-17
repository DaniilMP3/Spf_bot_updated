import sqlite3

from filters import IsAdmin, IsSuperUser
from aiogram import types
from create_bot import dp
from middleware.antiflood import rate_limit
from create_bot import cat_tree
from db_instance import db
from utils.exceptions import *
from utils.functions import pre_process_string
import logging


logger = logging.getLogger(__name__)


@dp.message_handler(IsSuperUser(), commands=['show_hierarchy'], chat_type=types.ChatType.PRIVATE)
@dp.message_handler(IsAdmin(), commands=['show_hierarchy'], chat_type=types.ChatType.PRIVATE)
@rate_limit(2, 'show_hierarchy')
async def show_hierarchy(message: types.Message):
    res = db.fetchall("SELECT * FROM specialities")
    if not res:
        await message.answer("No hierarchy now.")
        return
    tree = str(cat_tree)
    await message.answer(tree)


@dp.message_handler(IsSuperUser(), commands=['add_node'], chat_type=types.ChatType.PRIVATE)
@dp.message_handler(IsAdmin(), commands=['add_node'], chat_type=types.ChatType.PRIVATE)
@rate_limit(2, 'add_node')
async def add_node(message: types.Message):
    msg = await pre_process_string(message)

    split_msg = [w.strip() for w in msg.split(',')]
    split_len = len(split_msg)

    if split_len not in range(1, 3) or not msg:
        await message.answer("Incorrect format.")
    elif split_len == 1:
        try:
            speciality = split_msg[0]
            cat_tree.add_node(value=speciality)
        except sqlite3.IntegrityError as ie:
            await message.answer(str(ie), parse_mode="Markdown")
        else:
            await message.answer(f"Speciality *{speciality}* was added successfully!", parse_mode="Markdown")
            logger.info(f"Amin {message.from_user.full_name} add new speciality: {speciality}")

    else:
        try:
            group, speciality = split_msg[0], split_msg[1]
            cat_tree.add_node(value=group, parent=speciality)
        except (sqlite3.IntegrityError, ValueError) as er:
            await message.answer(str(er), parse_mode="Markdown")
        else:
            await message.answer(f"Group *{group}* was added successfully!", parse_mode="Markdown")
            logger.info(f"Amin {message.from_user.full_name} add new group: {group}")


@dp.message_handler(IsSuperUser(), commands=['edit_node'], chat_type=types.ChatType.PRIVATE)
@dp.message_handler(IsAdmin(), commands=['edit_node'], chat_type=types.ChatType.PRIVATE)
@rate_limit(2, 'edit_node')
async def edit_node(message: types.Message):
    msg = await pre_process_string(message)

    split_msg = [w.strip() for w in msg.split(',')]
    split_len = len(split_msg)

    if split_len not in range(2, 4) or not msg:
        await message.answer("Incorrect format.")
    elif split_len == 2:
        old_speciality, new_speciality = split_msg[0], split_msg[1]
        try:
            cat_tree.edit_node(old_value=old_speciality, new_value=new_speciality)
        except (ExistenceError, ValueError) as er:
            await message.answer(str(er), parse_mode="Markdown")
        else:
            await message.answer(f"Speciality *{old_speciality}* was edited to *{new_speciality}* successfully!",
                                 parse_mode="Markdown")
            logger.info(f"Amin {message.from_user.full_name} change old speciality {old_speciality} to: {new_speciality}")
    else:
        old_group, new_group, speciality = split_msg[0], split_msg[1], split_msg[2]
        try:
            cat_tree.edit_node(old_value=old_group, new_value=new_group, parent=speciality)
        except (ExistenceError, ValueError) as er:
            await message.answer(str(er), parse_mode="Markdown")
        else:
            await message.answer(f"Group *{old_group}* was edited to **{new_group}* successfully!",
                                 parse_mode="Markdown")
            logger.info(f"Amin {message.from_user.full_name} change old group {old_group} to: {new_group}")


@dp.message_handler(IsSuperUser(), commands=['delete_node'], chat_type=types.ChatType.PRIVATE)
@dp.message_handler(IsAdmin(), commands=['delete_node'], chat_type=types.ChatType.PRIVATE)
@rate_limit(2, 'delete_node')
async def delete_node(message: types.Message):
    msg = await pre_process_string(message)

    split_msg = [w.strip() for w in msg.split(',')]
    split_len = len(split_msg)

    if split_len not in range(1, 3) or not msg:
        await message.answer("Incorrect format.")
    elif split_len == 1:
        try:
            speciality = split_msg[0]
            cat_tree.delete_node(value=speciality)
        except(ExistenceError, ValueError) as er:
            await message.answer(str(er))
        else:
            await message.answer(f"Speciality *{speciality}* was deleted successfully!",
                                 parse_mode="Markdown")
            logger.info(f"Amin {message.from_user.full_name} delete speciality: {speciality}")
    else:
        try:
            group, speciality = split_msg[0], split_msg[1]
            cat_tree.delete_node(value=group, parent=speciality)
        except(ExistenceError, ValueError) as er:
            await message.answer(str(er))
        else:
            await message.answer(f"Group *{group}* was deleted successfully!",
                                 parse_mode="Markdown")
            logger.info(f"Amin {message.from_user.full_name} delete group: {group}")


@dp.message_handler(IsSuperUser(), commands=["delete_hierarchy"], chat_type=types.ChatType.PRIVATE)
@dp.message_handler(IsAdmin(), commands=["delete_hierarchy"], chat_type=types.ChatType.PRIVATE)
@rate_limit(2, "delete_hierarchy")
async def delete_hierarchy(message: types.Message):
    was_deleted = cat_tree.delete_all()
    if was_deleted:
        await message.answer("Hierarchy was fully deleted.")
        logger.info(f"Amin {message.from_user.full_name} delete the whole hierarchy")
        return
    await message.answer("Nothing to delete.")

