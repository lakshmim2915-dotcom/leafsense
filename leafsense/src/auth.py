import re, bcrypt
from .db import q, run

def register(username, email, password):
    if len(username) < 3: return False, "Username must be at least 3 characters."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): return False, "Invalid email."
    if len(password) < 8: return False, "Password must be at least 8 characters."
    if q("SELECT id FROM users WHERE username=:u OR email=:e", u=username, e=email):
        return False, "Username or email already exists."
    h = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    run("INSERT INTO users(username,email,password_hash) VALUES(:u,:e,:h)", u=username, e=email, h=h)
    return True, "Account created. Please log in."

def login(username, password):
    rows = q("SELECT id, username, password_hash FROM users WHERE username=:u", u=username)
    if rows and bcrypt.checkpw(password.encode(), rows[0]["password_hash"].encode()):
        return {"id": rows[0]["id"], "username": rows[0]["username"]}
    return None
