import datetime
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
from cfg import *
import logging

logger = logging.getLogger(__name__)


async def create_tasks(delay: Optional[int], args: List[tuple[Union[Callable, Awaitable], Optional[List[Any]]]]) -> None:

    """
    This function do some work with delay. Just creates task and execute it after delay.
    parameters: delay - time after which jobs are executing; args: List of jobs represented as tuples
    with one positional and two optional elements: first - object of function(also async).
    Second - arguments of a function.
    """
    if delay:
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


async def get_task_by_name(task_name: str) -> asyncio.Task:
    single_task_list = [task for task in asyncio.all_tasks() if task.get_name() == task_name]
    task = single_task_list.pop()
    return task


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


@dp.message_handler(InQueue(), commands=['find_partner'], chat_type=types.ChatType.PRIVATE)
@rate_limit(5, "find_partner")
async def deny_find_partner_by_accepted(message: types.Message):
    await message.answer("You accepted your meeting. Wait for your partner..")


@dp.message_handler(IsRegistered(), commands=['find_partner'], chat_type=types.ChatType.PRIVATE)
@rate_limit(5, "find_partner")
async def find_partner(message: types.Message):
    user_id1 = message.from_user.id
    loop = asyncio.get_event_loop()
    try:
        user1_pk, user2_pk, meeting_time, send_link_now, link1, link2 = await meetings_manager.create_meeting(user_id1)
        meeting_time_datetime, meeting_time_unix = meeting_time

        user_id2 = db.fetchone("SELECT telegram_id FROM users WHERE id = ?", (user2_pk,))[0]

        meetings_manager.list_append("is_choosing", user_id1)
        meetings_manager.list_append("is_choosing", user_id2)

        db.query("INSERT INTO meetings VALUES(?, ?, ?, ?, ?, ?)", (None, user1_pk,
                                                                   user2_pk, link1,
                                                                   link2, meeting_time_datetime
                                                                   ))
        meet_id = db.fetchone("SELECT last_insert_rowid()")[0]

        msg_success = f"Congrats! Meeting was created successfully! Start time: {meeting_time_datetime}.\n" \
                      f"Agree?"
        msg_failure = "Meeting was canceled. Try /find_partner again"

        kb1 = await getAcceptMessageKeyboard(send_link_now=send_link_now,
                                             meet_id=meet_id,
                                             candidate_id=user_id2,
                                             user_number="first_user")

        kb2 = await getAcceptMessageKeyboard(send_link_now=send_link_now,
                                             meet_id=meet_id,
                                             candidate_id=user_id1,
                                             user_number="second_user")

        msg1 = await bot.send_message(user_id1, msg_success, reply_markup=kb1)
        msg2 = await bot.send_message(user_id2, msg_success, reply_markup=kb2)

        meetings_manager.hset("message_ids", f"{user_id1}", msg1.message_id)
        meetings_manager.hset("message_ids", f"{user_id2}", msg2.message_id)
        # Task name here is ALWAYS message.from_user.id
        jobs = [(db.query, ["DELETE FROM meetings WHERE first_user = ?", (user1_pk,)]),
                (meetings_manager.list_lrem, ["is_choosing", 0, user_id1],),
                (meetings_manager.list_lrem, ["is_choosing", 0, user_id2]),
                (meetings_manager.list_lrem, ["accepted", 0, user_id1]),
                (meetings_manager.list_lrem, ["accepted", 0, user_id2]),
                (bot.send_message, [user_id1, msg_failure]),
                (bot.send_message, [user_id2, msg_failure]),
                (msg1.delete,),
                (msg2.delete,),
                (meetings_manager.hdel, ["message_ids", f"{user_id1}"]),
                (meetings_manager.hdel, ["message_ids", f"{user_id2}"])
                ]
        loop.create_task(create_tasks(60, jobs), name=f"{user_id1}")
        loop.create_task(create_tasks(60, jobs), name=f"{user_id2}")

    except ExistenceError:
        await message.answer("No candidate for you now, now you're in queue.")

    except GetTimeError as gte:
        await message.answer("Unable to get time now.")
        logger.error(str(gte))
    except:
        logger.exception("Unexpected exception in 'find_partner' handler")


@dp.callback_query_handler(acceptMessage_cb.filter(action="accept"))
async def find_partner_accept(query: types.CallbackQuery, callback_data: dict):
    await query.answer()

    user_id1 = query.from_user.id
    await bot.delete_message(chat_id=user_id1, message_id=query.message.message_id)

    loop = asyncio.get_event_loop()

    meetings_manager.list_lrem("is_choosing", 0, user_id1)
    meetings_manager.list_append("accepted", user_id1)

    task = await get_task_by_name(str(query.from_user.id))
    task.cancel()

    link1, link2, meeting_time = \
        db.fetchall("SELECT first_link, second_link, time FROM meetings where id = ?", (callback_data.get("meet_id"),))[0]

    if callback_data.get("user_number") == "second_user":  # Swap links if user is "second_user" in users table
        link1_copy = link1
        link1 = link2
        link2 = link1_copy

    user_id2 = callback_data.get("candidate_id")
    try:
        if not meetings_manager.value_exists("accepted", user_id2):
            await bot.send_message(user_id1, "Accepted!")
            await bot.send_message(user_id2, "Your partner is ready.")
        else:
            meetings_manager.list_lrem("accepted", 0, user_id1)
            meetings_manager.list_lrem("accepted", 0, user_id2)

            msg = "Your link:\n"
            if callback_data.get("send_link_now"):

                await bot.send_message(user_id1, "%s%s" % (msg, link1))
                await bot.send_message(user_id2, "%s%s" % (msg, link2))

                await create_tasks(JITSI_MEETING_TIME * 60, [(db.query, ["DELETE FROM meetings WHERE id = ?", (callback_data.get("meet_id"),)]
                                                              )])
            else:
                meetings_manager.hdel("message_ids", f"{user_id1}")
                meetings_manager.hdel("message_ids", f"{user_id2}")

                await bot.send_message(user_id1, "Link will be sent at meeting time")
                await bot.send_message(user_id2, "Link will be sent at meeting time")

                jobs = [(bot.send_message, [user_id1, "%s%s" % (msg, link1)]),
                        (bot.send_message, [user_id2, "%s%s" % (msg, link2)])]

                meeting_time_datetime = datetime.datetime.strptime(meeting_time, "%Y-%m-%d %H:%M:%S")

                meeting_time_unix = int(time.mktime(meeting_time_datetime.timetuple()))
                current_time_unix = int(time.time())

                loop.create_task(create_tasks(meeting_time_unix - current_time_unix, jobs))

                logger.info(f"New meeting was created. Users: {user_id1}, {user_id2}. Start time: {meeting_time}")

        await bot.delete_message(chat_id=query.message.from_user.id, message_id=query.message.message_id)
    except:
        logger.exception("Unexpected exception in 'find_partner_accept' handler")


@dp.callback_query_handler(acceptMessage_cb.filter(action="decline"))
async def find_partner_deny(query: types.CallbackQuery, callback_data: dict):
    await query.answer()
    try:
        task = await get_task_by_name(str(query.from_user.id))
        task.cancel()

        user_id1 = query.from_user.id
        user_id2 = callback_data.get("candidate_id")

        meetings_manager.list_lrem("is_choosing", 0, user_id1)
        meetings_manager.list_lrem("is_choosing", 0, user_id2)

        message_id1 = meetings_manager.hget("message_ids", f"{user_id1}")
        message_id2 = meetings_manager.hget("message_ids", f"{user_id2}")
        await bot.delete_message(chat_id=user_id1, message_id=message_id1)
        await bot.delete_message(chat_id=user_id2, message_id=message_id2)

        meetings_manager.hdel("message_ids", f"{user_id1}")
        meetings_manager.hdel("message_ids", f"{user_id2}")

        db.query("DELETE FROM meetings WHERE id = ?", (callback_data.get("meet_id"),))

        await bot.send_message(user_id1, "Meeting declined.")

        await bot.send_message(user_id2, 'Your partner decline meeting.\nTry /find_partner again')
    except:
        logger.exception("Unexpected exception in 'find_partner_deny' handler")
