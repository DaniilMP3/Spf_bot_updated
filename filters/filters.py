from aiogram.dispatcher.filters import Filter
from aiogram.types import Message
from create_bot import db


class IsRegistered(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id
        return bool(db.fetchone("SELECT * FROM users WHERE user_id = ?", user_id))
