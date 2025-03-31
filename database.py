import aiosqlite
import json

DATABASE = "data/bot.db"


async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                language TEXT DEFAULT 'en',
                coins TEXT DEFAULT '["bitcoin", "ethereum", "solana"]',
                premium BOOLEAN DEFAULT FALSE,
                notify_interval INTEGER DEFAULT 0,
                referrer_id INTEGER
            )
        ''')
        await db.commit()

async def add_user(user_id: int, username: str, referrer_id: int = None):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
            (user_id, username, referrer_id)
        )
        await db.commit()

async def get_referrer_id(user_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row and row[0] else None

async def set_language(user_id: int, language: str):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (language, user_id)
        )
        await db.commit()

async def get_language(user_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 'en'

async def count_users():
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        (count,) = await cursor.fetchone()
        return count

async def set_notify_interval(user_id: int, interval: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE users SET notify_interval = ? WHERE user_id = ?",
            (interval, user_id)
        )
        await db.commit()

async def get_users_for_notifications():
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE notify_interval > 0"
        )
        return [row[0] for row in await cursor.fetchall()]

async def set_user_coins(user_id: int, coins: list):
    coins_json = json.dumps(coins)
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE users SET coins = ? WHERE user_id = ?",
            (coins_json, user_id)
        )
        await db.commit()

async def get_user_coins(user_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user_id,)
        )
        result = await cursor.fetchone()
        return json.loads(result[0]) if result else ["bitcoin", "ethereum", "solana"]

async def set_user_premium(user_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("UPDATE users SET premium = TRUE WHERE user_id = ?", (user_id,))
        await db.commit()

async def is_user_premium(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute("SELECT premium FROM users WHERE user_id = ?", (user_id,))
        premium = await cursor.fetchone()
        return premium[0] if premium else False