from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiosqlite


class GoalManager:
    def __init__(self, bot, db_name):
        self.bot = bot
        self.db_name = db_name
        self.scheduler = AsyncIOScheduler()

    async def send_reminders(self):
        now = datetime.now()
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT id, user_id, message FROM reminders WHERE remind_at <= ?', (now,)) as cursor:
                reminders = await cursor.fetchall()

                for reminder in reminders:
                    reminder_id, user_id, message_text = reminder
                    await self.bot.send_message(user_id, message_text)
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
                    if deadline <= now:
                        remaining_amount = target_amount - current_amount
                        if remaining_amount > 0:
                            message_text = f"Вы не достигли цели '{goal_name}'. Осталось собрать {remaining_amount}."
                        else:
                            message_text = f"Поздравляем! Вы достигли цели '{goal_name}'."

                        await self.bot.send_message(user_id, message_text)
                        await db.execute('DELETE FROM financial_goals WHERE id = ?', (goal_id,))

            await db.commit()


    def start(self):
        self.scheduler.add_job(self.send_reminders, 'interval', minutes=1)
        self.scheduler.add_job(self.check_goals, 'interval', hours=1)
        self.scheduler.start()

