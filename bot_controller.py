from aiogram.types import ParseMode, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from States import AddIncome, AddExpense
from aiogram import types


class BotController:
    def __init__(self, bot, dp, finance_manager, currency_manager, db_manager):
        self.bot = bot
        self.dp = dp
        self.finance_manager = finance_manager
        self.currency_manager = currency_manager
        self.db_manager = db_manager

        self.register_handlers()

    categories_income = ["Зарплата", "Бонусы", "Подарки", "Инвестиции", "Другое"]
    categories_expense = ["Продукты", "Транспорт", "Развлечения", "Оплата жилья", "Другое"]

    async def set_commands(self):
        commands = [
            BotCommand(command="/start", description="Начало работы с ботом"),
            BotCommand(command="/rate", description="Получить курс валюты"),
            BotCommand(command="/convert", description="Конвертация сумм из одной валюты в другую"),
            BotCommand(command="/add_income", description="Добавить доход"),
            BotCommand(command="/add_expense", description="Добавить расход"),
            BotCommand(command="/statistics", description="Показать статистику")
        ]
        await self.bot.set_my_commands(commands)

    def register_handlers(self):
        self.dp.message_handler(commands=['start'])(self.send_welcome)
        self.dp.message_handler(commands=['rate'])(self.get_exchange_rate)
        self.dp.message_handler(commands=['convert'])(self.convert_currency)
        self.dp.message_handler(commands=['add_income'])(self.add_income_start)
        self.dp.message_handler(lambda message: message.text in self.finance_manager.categories_income,
                                state=AddIncome.category)(self.process_income_category)
        self.dp.message_handler(lambda message: message.text.isdigit(), state=AddIncome.amount)(
            self.process_income_amount)
        self.dp.message_handler(state=AddIncome.currency)(self.process_income_currency)
        self.dp.message_handler(commands=['add_expense'])(self.add_expense_start)
        self.dp.message_handler(lambda message: message.text in self.finance_manager.categories_expense,
                                state=AddExpense.category)(self.process_expense_category)
        self.dp.message_handler(lambda message: message.text.isdigit(), state=AddExpense.amount)(
            self.process_expense_amount)
        self.dp.message_handler(state=AddExpense.currency)(self.process_expense_currency)
        self.dp.message_handler(commands=['statistics'])(self.show_statistics)

    async def send_welcome(self, message: types.Message):
        await self.db_manager.add_user(message.from_user.id)

        welcome_text = (
            "Это Telegram-бот для управления личными финансами. Он помогает пользователям вести учет доходов и расходов, "
            "устанавливать финансовые цели и анализировать свои финансовые привычки. Позволяет пользователям отслеживать "
            "стоимость иностранных валют и учитывать свои транзакции в разных валютах. Основная цель бота — предоставить простой "
            "и удобный инструмент для контроля личных финансов и повышения финансовой грамотности.\n"
        )

        await message.answer(welcome_text, parse_mode='Markdown')

    async def get_exchange_rate(self, message: types.Message):
        if len(message.text.split()) != 2:
            await message.answer("Пожалуйста, используйте команду в формате /rate `<код_валюты>`."
                                 , parse_mode='Markdown')
            return

        try:
            _, currency_code = message.text.split()
            rate = self.currency_manager.get_rate(currency_code.upper())
            await message.answer(f"Текущий курс {currency_code.upper()} составляет {rate:.2f} RUB.",
                                 parse_mode='Markdown')
        except ValueError:
            await message.answer("Не удалось получить курс для указанной валюты. Проверьте код валюты.",
                                 parse_mode='Markdown')

    async def convert_currency(self, message: types.Message):
        if len(message.text.split()) != 4:
            await message.answer("Пожалуйста, используйте команду в формате /convert <сумма> <из_валюты> <в_валюту>."
                                 , parse_mode='Markdown')
            return

        try:
            _, amount, from_currency, to_currency = message.text.split()
            amount = float(amount)
            result = self.currency_manager.convert(amount, from_currency.upper(), to_currency.upper())
            await message.answer(f"{amount:.2f} {from_currency.upper()} = {result:.2f} {to_currency.upper()}",
                                 parse_mode='Markdown')
        except ValueError:
            await message.answer("Ошибка при конвертации. Пожалуйста, проверьте введенные данные.",
                                 parse_mode='Markdown')


    async def add_income_start(self, message: types.Message):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for category in self.finance_manager.categories_income:
            keyboard.add(KeyboardButton(category))
        await message.answer("Выберите категорию дохода:", reply_markup=keyboard, parse_mode='Markdown')
        await AddIncome.category.set()


    async def process_income_category(self, message: types.Message, state: FSMContext):
        await state.update_data(category=message.text)
        await message.answer("Введите сумму дохода:", reply_markup=types.ReplyKeyboardRemove(), parse_mode='Markdown')
        await AddIncome.amount.set()


    async def process_income_amount(self, message: types.Message, state: FSMContext):
        try:
            amount = float(message.text)
        except ValueError:
            await message.answer("Пожалуйста, введите корректное число.", parse_mode='Markdown')
            return
        await state.update_data(amount=amount)
        await message.answer("Введите валюту дохода:", parse_mode='Markdown')
        await AddIncome.currency.set()


    async def process_income_currency(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            category = data['category']
            amount = data['amount']
            currency = message.text
            await self.finance_manager.add_income(message.from_user.id, category, amount, currency)
        await state.finish()
        await message.answer("Доход успешно добавлен!", parse_mode='Markdown')


    async def add_expense_start(self, message: types.Message):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for category in self.finance_manager.categories_expense:
            keyboard.add(KeyboardButton(category))
        await message.answer("Выберите категорию расхода:", reply_markup=keyboard, parse_mode='Markdown')
        await AddExpense.category.set()


    async def process_expense_category(self, message: types.Message, state: FSMContext):
        if message.text not in self.finance_manager.categories_expense:
            await message.answer("Выберите категорию из предложенного списка.", parse_mode='Markdown')
            return
        await state.update_data(category=message.text)
        await AddExpense.next()
        await message.answer("Введите сумму расхода:", reply_markup=types.ReplyKeyboardRemove(), parse_mode='Markdown')


    async def process_expense_amount(self, message: types.Message, state: FSMContext):
        try:
            amount = float(message.text)
        except ValueError:
            await message.answer("Пожалуйста, введите корректное число.", parse_mode='Markdown')
            return
        await state.update_data(amount=amount)
        await AddExpense.next()
        await message.answer("Введите валюту расхода:", parse_mode='Markdown')


    async def process_expense_currency(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            category = data['category']
            amount = data['amount']
            currency = message.text
            await self.finance_manager.add_expense(message.from_user.id, category, amount, currency)
        await state.finish()
        await message.answer("Расход успешно добавлен!", parse_mode='Markdown')


    async def show_statistics(self, message: types.Message):
        stats = await self.finance_manager.get_statistics(message.from_user.id)

        image_data = await self.finance_manager.create_statistics_chart(message.from_user.id)

        await message.answer(stats, parse_mode='Markdown')

        await message.answer_photo(image_data, caption="Диаграмма доходов и расходов", parse_mode='Markdown')
