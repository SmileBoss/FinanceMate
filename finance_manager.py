import datetime
import io

import aiosqlite
from matplotlib import pyplot as plt


class FinanceManager:
    def __init__(self, db_name):
        self.db_name = db_name


    async def get_user_id(self, telegram_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
                user = await cursor.fetchone()
                if user:
                    return user[0]
                else:
                    await db.execute('INSERT INTO users (telegram_id) VALUES (?)', (telegram_id,))
                    await db.commit()
                    async with db.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
                        user = await cursor.fetchone()
                        return user[0]


    async def add_income(self, telegram_id, category, amount, currency):
        user_id = await self.get_user_id(telegram_id)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO income (user_id, category, amount, currency, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, category, amount, currency, datetime.datetime.now().isoformat()))
            await db.commit()


    async def add_expense(self, telegram_id, category, amount, currency):
        user_id = await self.get_user_id(telegram_id)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO expenses (user_id, category, amount, currency, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, category, amount, currency, datetime.datetime.now().isoformat()))
            await db.commit()


    async def get_statistics(self, telegram_id):
        user_id = await self.get_user_id(telegram_id)
        income_data = []
        expenses_data = []
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT category, amount, currency, date FROM income WHERE user_id = ?',
                                  (user_id,)) as cursor:
                income_data = await cursor.fetchall()
            async with db.execute('SELECT category, amount, currency, date FROM expenses WHERE user_id = ?',
                                  (user_id,)) as cursor:
                expenses_data = await cursor.fetchall()

        statistics = "Статистика доходов и расходов:\n\nДоходы:\n"
        for category, amount, currency, date in income_data:
            statistics += f"{category}: {amount} {currency} (Дата: {date})\n"

        statistics += "\nРасходы:\n"
        for category, amount, currency, date in expenses_data:
            statistics += f"{category}: {amount} {currency} (Дата: {date})\n"

        return statistics

    async def create_statistics_chart(self, telegram_id):
        user_id = await self.get_user_id(telegram_id)

        income_data = {}
        expenses_data = {}

        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT category, amount FROM income WHERE user_id = ?', (user_id,)) as cursor:
                async for row in cursor:
                    category, amount = row
                    if category in income_data:
                        income_data[category] += amount
                    else:
                        income_data[category] = amount

            async with db.execute('SELECT category, amount FROM expenses WHERE user_id = ?', (user_id,)) as cursor:
                async for row in cursor:
                    category, amount = row
                    if category in expenses_data:
                        expenses_data[category] += amount
                    else:
                        expenses_data[category] = amount

        # Создание двух графиков: один для доходов, другой для расходов
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

        # График доходов
        ax1.pie(income_data.values(), labels=income_data.keys(), autopct='%1.1f%%', startangle=140)
        ax1.set_title('Доходы по категориям')

        # График расходов
        ax2.pie(expenses_data.values(), labels=expenses_data.keys(), autopct='%1.1f%%', startangle=140)
        ax2.set_title('Расходы по категориям')

        # Сохранение изображения в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)

        return buf
