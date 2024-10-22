import aiosqlite


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path


    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id INTEGER NOT NULL UNIQUE
                        )
                    ''')
            await db.execute('''
                                CREATE TABLE IF NOT EXISTS income (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER,
                                    category TEXT,
                                    amount REAL,
                                    currency TEXT,
                                    date TEXT,
                                    FOREIGN KEY(user_id) REFERENCES users(id)
                                )
                            ''')
            await db.execute('''
                                CREATE TABLE IF NOT EXISTS expenses (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER,
                                    category TEXT,
                                    amount REAL,
                                    currency TEXT,
                                    date TEXT,
                                    FOREIGN KEY(user_id) REFERENCES users(id)
                                )
                            ''')
            await db.execute('''
                        CREATE TABLE IF NOT EXISTS financial_goals (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            goal_name TEXT,
                            target_amount REAL,
                            deadline DATE,
                            current_amount REAL DEFAULT 0,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        )
            ''')
            await db.execute('''
                        CREATE TABLE IF NOT EXISTS reminders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            message TEXT,
                            remind_at TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        )
            ''')
            await db.commit()


    async def add_user(self, telegram_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (telegram_id,))
            await db.commit()

