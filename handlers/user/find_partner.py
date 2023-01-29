import time

from filters import *
from aiogram import types
from create_bot import dp, meetings_manager, bot
from utils.exceptions import *
from aiogram.dispatcher import FSMContext
import asyncio
from typing import Optional, Union, Callable, List, Any, Awaitable, Literal
from middleware.antiflood import rate_limit
from aiogram.dispatcher.filters import Text
from keyboards import getAcceptMessageKeyboard, acceptMessage_cb
from utils.data_classes import QueueUser


async def create_task_with_delay(delay: int, args: List[tuple[Union[Callable, Awaitable], Optional[List[Any]]]]):
    await asyncio.sleep(delay)
    for job in args:
        func = job[0]
        if len(job) > 1:
            arguments = job[1]
            if asyncio.iscoroutinefunction(func):
                await func(*arguments)
            else:
                func(*arguments)
        else:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()


async def send_acceptMessage_with_delay(delay: int, user_id: int, msg: str, kb: Optional[Union[types.ReplyKeyboardMarkup,
                                                                                               types.InlineKeyboardMarkup]] = None):
    await asyncio.sleep(delay)
    if kb:
        await bot.send_message(user_id, msg, reply_markup=kb)
        return
    await bot.send_message(user_id, msg)


@dp.message_handler(IsNotRegistered(), commands=['find_partner'], chat_type=types.ChatType.PRIVATE)
@rate_limit(5, "find_partner")
async def deny_find_partner_by_registration(message: types.Message):
    await message.answer("You are not registered.")


@dp.message_handler(IsChoosing(), commands=['find_partner'], chat_type=types.ChatType.PRIVATE)
@rate_limit(5, "find_partner")
async def deny_find_partner_by_waitingRoom(message: types.Message):
    await message.answer("You are waiting for meeting.")


@dp.message_handler(InQueue(), commands=['find_partner'], chat_type=types.ChatType.PRIVATE)
@rate_limit(5, "find_partner")
async def deny_find_partner_by_queue(message: types.Message):
    await message.answer("You already in queue.")


@dp.message_handler(IsRegistered(), commands=['find_partner'], chat_type=types.ChatType.PRIVATE)
@rate_limit(5, "find_partner")
async def find_partner(message: types.Message, state: FSMContext):
    user_id1 = message.from_user.id
    loop = asyncio.get_event_loop()
    try:
        meeting_time_datetime, meeting_time_unix, user1_pk, user2_pk, link1, link2 = \
            await meetings_manager.create_meeting(user_id=user_id1)

        user_id2 = db.fetchone("SELECT telegram_id FROM users WHERE id = ?", (user2_pk,))[0]

        meetings_manager.list_append("is_choosing", user_id1)
        meetings_manager.list_append("is_choosing", user_id2)

        db.query("INSERT INTO meetings VALUES(?, ?, ?, ?, ?, ?)", (None, user1_pk,
                                                                         user2_pk, link1,
                                                                         link2, meeting_time_datetime
                                                                         ))

        msg = f"Congrats! Meeting was created successfully! Start time: {meeting_time_datetime}.\n" \
              f"Agree?"

        jobs1 = [(db.query, ["DELETE FROM meetings WHERE first_user = ?", (user1_pk,)]),
                 (bot.send_message, [user_id1, "Deleted."])]

        jobs2 = [(db.query, ["DELETE FROM meetings WHERE first_user = ?", (user1_pk,)]),
                 (bot.send_message, [user_id2, "Deleted."])]

        task1 = loop.create_task(create_task_with_delay(15, jobs1), name=f"{user_id1}")
        task2 = loop.create_task(create_task_with_delay(15, jobs2), name=f"{user_id2}")

        kb1 = await getAcceptMessageKeyboard(user1_pk, user_id2, "first_user", task1.get_name())
        kb2 = await getAcceptMessageKeyboard(user2_pk, user_id1, "second_user", task2.get_name())
        await bot.send_message(user_id1, msg, reply_markup=kb1)
        await bot.send_message(user_id2, msg, reply_markup=kb2)

    except ExistenceError:
        await message.answer("No candidate for you now, now you're in queue.")

    except GetTimeError:
        await message.answer("For today meetings are over.")


@dp.callback_query_handler(acceptMessage_cb.filter())
async def test(query: types.CallbackQuery, callback_data: dict):
    user_id1 = query.from_user.id
    await query.answer()
    await bot.delete_message(chat_id=user_id1, message_id=query.message.message_id)

    user_id2, task_name = callback_data.get("candidate_id"), callback_data.get("task")

    single_task_list = [task for task in asyncio.all_tasks() if task.get_name() == task_name]
    task = single_task_list.pop()

    meetings_manager.list_lrem("is_choosing", 0, user_id1)
    meetings_manager.list_append("accepted", user_id1)

    task.cancel()
    user2_pk = callback_data.get("candidate_pk")
    if callback_data.get("action") == "accept":
        ##To do: specify time when send message with links depending on delay
        if not meetings_manager.value_exists("accepted", user_id2):
            await bot.send_message(user_id1, "Accepted!")
            await bot.send_message(user_id2, "Your partner is ready.")
        else:
            meetings_manager.list_lrem("accepted", 0, user_id1)
            meetings_manager.list_lrem("accepted", 0, user_id2)

            links_res = db.fetchone("SELECT first_link, second_link FROM meetings WHERE first_user = ? or second_user = ?", (user2_pk, user2_pk))
            link1, link2 = links_res[0], links_res[1]
            msg = "Your link:\n"

            await bot.send_message(user_id1, "%s%s" % (msg, link1))
            await bot.send_message(user_id2, "%s%s" % (msg, link2))

    else:
        meetings_manager.list_lrem(user_id2)
        db.query("DELETE FROM meetings WHERE first_user = ? or second_user = ?", (user2_pk, user2_pk))

        await bot.send_message(user_id1, "Meeting declined.")

        await bot.send_message(user_id2, 'Your partner decline meeting. Try /find_partner again')




