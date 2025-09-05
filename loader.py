from aiogram import Bot,Dispatcher
from data.config import BOT_TOKEN
from aiogram.fsm.storage.memory import MemoryStorage
import aioredis


bot = Bot(token=BOT_TOKEN,parse_mode='HTML')
redis = aioredis.from_url("redis://localhost", decode_responses=True)
dp = Dispatcher(storage=MemoryStorage())
