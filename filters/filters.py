from aiogram.dispatcher.filters import Filter
from aiogram.types import Message
from create_bot import ADMINS
from db_instance import db


class IsRegistered(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id

        return bool(db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,)))


class IsNotRegistered(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id

        return not bool(db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,)))


class IsAdmin(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id
        return user_id in ADMINS


class IsUser(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id
        return user_id not in ADMINS
