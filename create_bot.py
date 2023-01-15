from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from os import getenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils import Hierarchy, MeetingsManager
import redis


load_dotenv()

ADMINS = []

bot = Bot(token=getenv("TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())
cat_tree = Hierarchy()

redis_client = redis.Redis(host="localhost", port=6379, db=0)
meetings_manager = MeetingsManager(redis_client)


