from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from os import getenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils import Hierarchy


load_dotenv()

ADMINS = []

bot = Bot(token=getenv("TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())
cat_tree = Hierarchy()

