from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from os import getenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils import Database


load_dotenv()

ADMINS = []

bot = Bot(token=getenv("TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database("data/database.db")
