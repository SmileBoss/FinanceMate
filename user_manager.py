import aiosqlite



class UserManager:
    def __init__(self, db_name):
        self.db_name = db_name

    async def add_user(self, telegram_id: int):

        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (telegram_id,))
            await db.commit()

    async def get_user_id(self, telegram_id: int):

        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
                user = await cursor.fetchone()
                if user:
                    return user[0]
                else:
                    # User doesn't exist, add them
                    await db.execute('INSERT INTO users (telegram_id) VALUES (?)', (telegram_id,))
                    await db.commit()
                    # Retrieve the new user ID
                    async with db.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
                        user = await cursor.fetchone()
                        return user[0]

    async def get_telegram_id(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT telegram_id FROM users WHERE id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    try:
                        # Преобразование в int перед возвратом
                        return int(row[0])
                    except ValueError:
                        raise ValueError(f"Telegram ID для пользователя с id {user_id} не является целым числом.")
                else:
                    raise ValueError(f"Пользователь с id {user_id} не найден.")
