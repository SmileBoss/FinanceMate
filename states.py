from aiogram.dispatcher.filters.state import StatesGroup, State


class AddIncome(StatesGroup):
    category = State()
    amount = State()
    currency = State()


class AddExpense(StatesGroup):
    category = State()
    amount = State()
    currency = State()
