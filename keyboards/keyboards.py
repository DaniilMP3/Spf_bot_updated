from aiogram import types
from db_instance import db
from typing import Literal, Optional
from aiogram.utils.callback_data import CallbackData


sex_kb = types.ReplyKeyboardMarkup().add("Male", "Female")


cancel_cross = "❌"
previous_state = "👈"

sex_kb.add(cancel_cross, previous_state)

empty_kb = types.ReplyKeyboardMarkup().add(cancel_cross, previous_state)


async def getSpecialitiesKeyboard():
    specialities = [types.KeyboardButton(s[1]) for s in db.fetchall("SELECT * FROM specialities")]

    kb = types.ReplyKeyboardMarkup(keyboard=[specialities])
    kb.add(cancel_cross, previous_state)
    return kb


async def getGroupsKeyboard(speciality_id):
    groups = [types.KeyboardButton(g[1]) for g in db.fetchall("SELECT * FROM users_groups WHERE parent_speciality = ?", (speciality_id,))]

    kb = types.ReplyKeyboardMarkup(keyboard=[groups])
    kb.add(cancel_cross, previous_state)
    return kb

acceptMessage_cb = CallbackData("acceptMessage_cb", #prefix
                                "action",
                                "send_link_now",
                                "meet_id",
                                "user_number",
                                "candidate_id"
                                )


async def getAcceptMessageKeyboard(send_link_now: bool, meet_id: int, candidate_id: int,
                                   user_number: Literal["first_user", "second_user"]):

    kb = types.InlineKeyboardMarkup()

    accept_button = types.InlineKeyboardButton("Accept", callback_data=acceptMessage_cb.new(action="accept",
                                                                                            send_link_now=send_link_now,
                                                                                            meet_id=meet_id,
                                                                                            candidate_id=candidate_id,
                                                                                            user_number=user_number))

    decline_button = types.InlineKeyboardButton("Decline", callback_data=acceptMessage_cb.new(action="decline",
                                                                                              send_link_now=send_link_now,
                                                                                              meet_id=meet_id,
                                                                                              candidate_id=candidate_id,
                                                                                              user_number=user_number,
                                                                                              ))
    # Actually, message_id_to_delete key is needed when user denied meeting,
    # and we need to delete previous message with keyboard

    kb.add(accept_button, decline_button)
    return kb
