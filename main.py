import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from dotenv import load_dotenv

from bot_controller import BotController
from currency_manager import CurrencyManager
from database_manager import DatabaseManager
from finance_manager import FinanceManager
from goal_manager import GoalManager
from user_manager import UserManager

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

user_manager = UserManager("./app_data/finances.db")
finance_manager = FinanceManager("./app_data/finances.db")
currency_manager = CurrencyManager()
db_manager = DatabaseManager('./app_data/finances.db')
goal_manager = GoalManager(bot, './app_data/finances.db')

bot_controller = BotController(bot, dp, finance_manager, currency_manager, db_manager, goal_manager, user_manager)


async def on_startup(dispatcher):
    await bot_controller.set_commands()

    await db_manager.init_db()

    goal_manager.start()

    print("Бот успешно запущен!")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)

