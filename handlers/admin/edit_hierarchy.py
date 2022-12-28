import re
from filters import IsAdmin
from aiogram import types
from create_bot import dp
from middleware.antiflood import rate_limit
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from create_bot import cat_tree
from db_instance import db


async def pre_process_string(message):
    command = message.get_command()
    msg = message.text
    msg = re.sub(r'\s+', ' ', msg.strip())
    msg = msg.replace(command, '')
    return msg


@dp.message_handler(commands=['show_hierarchy'])
@rate_limit(2, 'show_hierarchy')
async def show_hierarchy(message: types.Message):
    res = db.fetchall("SELECT * FROM specialities")
    if not res:
        await message.answer("No hierarchy now.")
        return
    tree = str(cat_tree)
    print(tree)


@dp.message_handler(commands=['add_node'])
@dp.message_handler(commands=['edit_node'])
@rate_limit(3)
async def add_or_edit(message: types.Message):
    command = message.get_command()
    msg = await pre_process_string(message)

    split_msg = [w.strip() for w in msg.split(',')]
    split_len = len(split_msg)

    if command.startswith("/add"):
        if split_len not in range(1, 3) or not msg:
            await message.answer("Incorrect format.")

        elif split_len == 1:
            speciality = split_msg[0]
            was_added = cat_tree.add_node(value=speciality)
            if was_added:
                await message.answer("Speciality was added successfully!")
            else:
                await message.answer("Speciality already exists.")
        else:
            group = split_msg[0]
            speciality = split_msg[1]
            was_added = cat_tree.add_node(value=group, parent=speciality)
            if was_added:
                await message.answer("Group was added successfully!")
            else:
                await message.answer("Group already exists or parent speciality doesn't exists.")

    elif command.startswith("/edit"):
        if split_len not in range(2, 4):
            await message.answer("Incorrect format.")

        elif split_len == 2:
            old_speciality, new_speciality = split_msg[0], split_msg[1]
            was_edited = cat_tree.edit_node(old_speciality, new_speciality)
            if was_edited:
                await message.answer("Speciality was edited successfully!")
            else:
                await message.answer("Speciality doesn't exists.")
        else:
            old_group, new_group = split_msg[0], split_msg[1]
            speciality = split_msg[2]
            print(split_msg)
            was_edited = cat_tree.edit_node(old_group, new_group, parent=speciality)
            if was_edited:
                await message.answer("Group was edited successfully!")
            else:
                await message.answer("Parent speciality or group do not exists.")


@dp.message_handler(commands=['delete_node'])
@rate_limit(3, 'delete_node')
async def delete_node(message: types.Message):
    msg = await pre_process_string(message)

    split_msg = [w.strip() for w in msg.split(',')]
    split_len = len(split_msg)

    if split_len not in range(1, 3) or not msg:
        await message.answer("Incorrect format.")
    elif split_len == 1:
        speciality = split_msg[0]
        was_deleted = cat_tree.delete_node(value=speciality)

        if was_deleted:
            await message.answer("Speciality and all child groups was deleted successfully!")
        else:
            await message.answer("Speciality doesn't exists.")
    else:
        group, speciality = split_msg[0], split_msg[1]
        was_deleted = cat_tree.delete_node(value=group, parent=speciality)
        if was_deleted:
            await message.answer("Group was deleted successfully!")
        else:
            await message.answer("Speciality or group do not exists.")
