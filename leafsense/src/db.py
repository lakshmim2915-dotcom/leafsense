import os, re
import pymysql
from pymysql.cursors import DictCursor

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

def _conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "leafsense"),
        cursorclass=DictCursor, autocommit=True, charset="utf8mb4")

def _fmt(sql):
    # turn :name placeholders into PyMySQL's %(name)s
    return re.sub(r"(?<!:):(\w+)", r"%(\1)s", sql)

def q(sql, **p):
    """SELECT -> list of dict rows."""
    con = _conn()
    try:
        with con.cursor() as cur:
            cur.execute(_fmt(sql), p)
            return list(cur.fetchall())
    finally:
        con.close()

def run(sql, **p):
    """INSERT/UPDATE/DELETE -> lastrowid."""
    con = _conn()
    try:
        with con.cursor() as cur:
            cur.execute(_fmt(sql), p)
            return cur.lastrowid
    finally:
        con.close()