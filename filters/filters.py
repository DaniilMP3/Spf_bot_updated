from aiogram.dispatcher.filters import Filter
from aiogram.types import Message
from create_bot import ADMINS, meetings_manager
from db_instance import db
from ast import literal_eval


class IsRegistered(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id

        return bool(db.fetchone("SELECT * FROM users WHERE telegram_id = ?", (user_id,)))


class IsNotRegistered(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id

        return not bool(db.fetchone("SELECT * FROM users WHERE telegram_id = ?", (user_id,)))


class IsAdmin(Filter):
    async def check(self, message: Message):
        return bool(db.fetchone("SELECT * FROM admins WHERE telegram_id = ?", (message.from_user.id,)))


class IsSuperUser(Filter):
    async def check(self, message: Message):
        is_super_user = db.fetchone("SELECT is_super_user FROM admins WHERE telegram_id = ?", (message.from_user.id,))
        if not is_super_user:
            return False
        if is_super_user[0] == 0:
            return False
        else:
            return True


class IsUser(Filter):
    async def check(self, message: Message):
        user_id = message.from_user.id
        return user_id not in ADMINS


class InQueue(Filter):
    async def check(self, message: Message):
        queue_str = [i.decode('utf-8') for i in meetings_manager.lrange("queue", 0, -1)]
        queue_ids = [literal_eval(i)["user_id"] for i in queue_str]
        return message.from_user.id in queue_ids


class IsChoosing(Filter):
    async def check(self, message: Message):
        return meetings_manager.value_exists_in_list("is_choosing", message.from_user.id)


class IsAccepted(Filter):
    async def check(self, message: Message):
        return meetings_manager.value_exists_in_list("accepted", message.from_user.id)


class OnMeeting(Filter):
    async def check(self, message: Message):
        return meetings_manager.value_exists_in_list("on_meeting", message.from_user.id)
