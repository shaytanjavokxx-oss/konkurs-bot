import sqlite3
from datetime import datetime

DB = "konkurs.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        phone TEXT,
        ball INTEGER DEFAULT 0,
        referrer_id INTEGER DEFAULT 0,
        sana TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        referred_id INTEGER,
        sana TEXT
    )''')
    conn.commit()
    conn.close()

def user_qoshish(user_id, username, first_name, referrer_id=0):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name, ball, referrer_id, sana)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id, username or "", first_name or "", 5, referrer_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()

def user_olish(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def phone_saqlash(user_id, phone):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET phone=? WHERE user_id=?", (phone, user_id))
    conn.commit()
    conn.close()

def ball_qoshish(user_id, ball):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET ball=ball+? WHERE user_id=?", (ball, user_id))
    conn.commit()
    conn.close()

def referral_qoshish(user_id, referred_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id FROM referrals WHERE user_id=? AND referred_id=?", (user_id, referred_id))
    if not c.fetchone():
        c.execute("INSERT INTO referrals (user_id, referred_id, sana) VALUES (?, ?, ?)",
                  (user_id, referred_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def top_users(limit=10):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, ball FROM users ORDER BY ball DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def jami_users():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    n = c.fetchone()[0]
    conn.close()
    return n

def barcha_users():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, ball, phone FROM users ORDER BY ball DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def referral_soni(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE user_id=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n
