from aiogram import types
from db_instance import db

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
