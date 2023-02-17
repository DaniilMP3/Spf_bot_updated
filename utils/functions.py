import re
from aiogram.types import Message


async def pre_process_string(message: Message):
    command = message.get_command()
    msg = message.text
    msg = re.sub(r'\s+', ' ', msg.strip())
    msg = msg.replace(command, '')
    return msg
