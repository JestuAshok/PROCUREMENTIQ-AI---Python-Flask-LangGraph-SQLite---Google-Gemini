import os
import sqlite3
from pathlib import Path
from flask import g, current_app

def get_db_path():
    if current_app:
        db_path = current_app.config.get('DATABASE_PATH')
    else:
        from config import Config
        db_path = Config.DATABASE_PATH
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    return db_path

def get_db():
    if 'db' not in g:
        db_path = get_db_path()
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    db_path = app.config['DATABASE_PATH'] if app else get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    schema_path = Path(__file__).resolve().parent / 'schema.sql'
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), commit=True):
    db = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id
