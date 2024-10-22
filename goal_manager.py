from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from user_manager import UserManager
import aiosqlite


class GoalManager:
    def __init__(self, bot, db_name):
        self.bot = bot
        self.db_name = db_name
        self.scheduler = AsyncIOScheduler()
        self.user_manager = UserManager(db_name)

    async def send_reminders(self):
        now = datetime.now()
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT id, user_id, message FROM reminders WHERE remind_at <= ?', (now,)) as cursor:
                reminders = await cursor.fetchall()
                for reminder in reminders:
                    reminder_id, user_id, message_text = reminder
                    telegram_id = await self.user_manager.get_telegram_id(user_id)
                    await self.bot.send_message(telegram_id, message_text)
                    await db.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))

            await db.commit()

    async def check_goals(self):
        now = datetime.now()
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                    'SELECT id, user_id, goal_name, target_amount, deadline, current_amount FROM financial_goals') as cursor:
                goals = await cursor.fetchall()

                for goal in goals:
                    goal_id, user_id, goal_name, target_amount, deadline, current_amount = goal
                    deadline_dt = datetime.strptime(deadline, '%Y-%m-%d')
                    if deadline_dt <= now:
                        remaining_amount = target_amount - current_amount
                        if remaining_amount > 0:
                            message_text = f"Вы не достигли цели '{goal_name}'. Осталось собрать {remaining_amount}."
                        else:
                            message_text = f"Поздравляем. Вы достигли цели '{goal_name}'."

                        message_text = message_text.replace(".", "\\.").replace("-", "\\-")
                        telegram_id = await self.user_manager.get_telegram_id(user_id)
                        await self.bot.send_message(telegram_id, message_text)
                        await db.execute('DELETE FROM financial_goals WHERE id = ?', (goal_id,))

            await db.commit()

    async def set_financial_goal(self, telegram_id, goal_name, target_amount, deadline):
        user_id = await self.user_manager.get_user_id(telegram_id)

        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Дата должна быть в формате YYYY-MM-DD.")

        # Вставляем финансовую цель в базу данных
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO financial_goals (user_id, goal_name, target_amount, deadline)
                VALUES (?, ?, ?, ?)
            ''', (user_id, goal_name, target_amount, deadline_date))
            await db.commit()

    async def add_reminder(self, telegram_id, message, remind_at):
        user_id = await self.user_manager.get_user_id(telegram_id)

        try:
            remind_at_datetime = datetime.fromisoformat(remind_at)
        except ValueError:
            raise ValueError("Дата и время должны быть в формате YYYY-MM-DDTHH:MM:SS.")

        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO reminders (user_id, message, remind_at)
                VALUES (?, ?, ?)
            ''', (user_id, message, remind_at_datetime))
            await db.commit()

    async def get_financial_goals(self, telegram_id):
        user_id = await self.user_manager.get_user_id(telegram_id)
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                    'SELECT id, goal_name, target_amount, deadline, current_amount FROM financial_goals WHERE user_id = ?',
                    (user_id,)) as cursor:
                goals = await cursor.fetchall()
                return [
                    {
                        "id": goal[0],
                        "goal_name": goal[1],
                        "target_amount": goal[2],
                        "deadline": goal[3],
                        "current_amount": goal[4],
                    }
                    for goal in goals
                ]

    async def contribute_to_goal(self, telegram_id, goal_id: int, amount: float):
        user_id = await self.user_manager.get_user_id(telegram_id)
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT current_amount FROM financial_goals WHERE id = ? AND user_id = ?',
                                  (goal_id, user_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    current_amount = row[0]
                    new_amount = current_amount + amount
                    await db.execute('UPDATE financial_goals SET current_amount = ? WHERE id = ? AND user_id = ?',
                                     (new_amount, goal_id, user_id))
                    await db.commit()
                    return new_amount
                else:
                    raise ValueError(f"Финансовая цель с id {goal_id} для пользователя {user_id} не найдена.")

    def start(self):
        self.scheduler.add_job(self.send_reminders, 'interval', minutes=1)
        self.scheduler.add_job(self.check_goals, 'interval', minutes=1)
        self.scheduler.start()

