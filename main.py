import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor

from BotController import BotController
from CurrencyManager import CurrencyManager
from DatabaseManager import DatabaseManager
from FinanceManager import FinanceManager

API_TOKEN = '7718869677:AAF7481qS0dyQOI6m237cQLyok8Qy5QPFhE'

# Задаем уровень логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Инициализация менеджеров
finance_manager = FinanceManager("finances.db")
currency_manager = CurrencyManager()
db_manager = DatabaseManager('finances.db')

# Определение и инициализация контроллера
bot_controller = BotController(bot, dp, finance_manager, currency_manager, db_manager)


async def on_startup(dispatcher):
    # Установить команды при старте
    await bot_controller.set_commands()

    # Инициализация БД если необходимо
    await db_manager.init_db()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
