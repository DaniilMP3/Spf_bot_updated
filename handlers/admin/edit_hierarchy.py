import re
import sqlite3

from filters import IsAdmin
from aiogram import types
from create_bot import dp
from middleware.antiflood import rate_limit
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from create_bot import cat_tree
from db_instance import db
from utils.exceptions import *


async def pre_process_string(message):
    command = message.get_command()
    msg = message.text
    msg = re.sub(r'\s+', ' ', msg.strip())
    msg = msg.replace(command, '')
    return msg


@dp.message_handler(commands=['show_hierarchy'], chat_type=types.ChatType.PRIVATE)
@rate_limit(2, 'show_hierarchy')
async def show_hierarchy(message: types.Message):
    res = db.fetchall("SELECT * FROM specialities")
    if not res:
        await message.answer("No hierarchy now.")
        return
    tree = str(cat_tree)
    await message.answer(tree)


@dp.message_handler(commands=['add_node'], chat_type=types.ChatType.PRIVATE)
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

    else:
        try:
            group, speciality = split_msg[0], split_msg[1]
            cat_tree.add_node(value=group, parent=speciality)
        except (sqlite3.IntegrityError, ValueError) as er:
            await message.answer(str(er), parse_mode="Markdown")
        else:
            await message.answer(f"Group *{group}* was added successfully!", parse_mode="Markdown")


@dp.message_handler(commands=['edit_node'], chat_type=types.ChatType.PRIVATE)
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
    else:
        old_group, new_group, speciality = split_msg[0], split_msg[1], split_msg[2]
        try:
            cat_tree.edit_node(old_value=old_group, new_value=new_group, parent=speciality)
        except (ExistenceError, ValueError) as er:
            await message.answer(str(er), parse_mode="Markdown")
        else:
            await message.answer(f"Group *{old_group}* was edited to **{new_group}* successfully!",
                                 parse_mode="Markdown")


@dp.message_handler(commands=['delete_node'], chat_type=types.ChatType.PRIVATE)
@rate_limit(3, 'delete_node')
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
    else:
        try:
            group, speciality = split_msg[0], split_msg[1]
            cat_tree.delete_node(value=group, parent=speciality)
        except(ExistenceError, ValueError) as er:
            await message.answer(str(er))
        else:
            await message.answer(f"Group *{group}* was deleted successfully!",
                                 parse_mode="Markdown")


@dp.message_handler(commands=["delete_hierarchy"], chat_type=types.ChatType.PRIVATE)
@rate_limit(3, "delete_hierarchy")
async def delete_hierarchy(message: types.Message):
    was_deleted = cat_tree.delete_all()
    if was_deleted:
        await message.answer("Hierarchy was fully deleted.")
        return
    await message.answer("Nothing to delete.")
