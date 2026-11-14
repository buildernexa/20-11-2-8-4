# language: Python, file: core/history.py
import sqlite3, os, datetime
DB = "data/history.db"

def _conn():
    os.makedirs("data", exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT, title TEXT, author TEXT, source TEXT,
        status TEXT, ts TEXT
    )""")
    return c

def log(url, title, author, source, status="ok"):
    with _conn() as c:
        c.execute("INSERT INTO history(url,title,author,source,status,ts) VALUES(?,?,?,?,?,?)",
                  (url, title, author, source, status,
                   datetime.datetime.utcnow().isoformat(timespec="seconds")))

def recent(limit=50):
    with _conn() as c:
        return c.execute("SELECT url,title,author,source,status,ts FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

def clear():
    with _conn() as c:
        c.execute("DELETE FROM history")
