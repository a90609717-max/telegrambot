# database.py - База даних для бота Карта Тривог
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import contextmanager

DB_FILE = Path("alerts_bot.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                regions TEXT DEFAULT '',
                role TEXT DEFAULT 'user',
                notifications_enabled INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                uid TEXT UNIQUE,
                alert_status TEXT DEFAULT 'N',
                last_updated TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shelters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                city TEXT NOT NULL,
                address TEXT NOT NULL,
                shelter_type TEXT DEFAULT 'укриття',
                capacity INTEGER DEFAULT 0,
                lat REAL,
                lon REAL,
                description TEXT
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                sent_by TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recipients_count INTEGER DEFAULT 0
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        regions_data = [
            ("Вінницька область", "1"),
            ("Волинська область", "2"),
            ("Дніпропетровська область", "3"),
            ("Донецька область", "4"),
            ("Житомирська область", "5"),
            ("Закарпатська область", "6"),
            ("Запорізька область", "7"),
            ("Івано-Франківська область", "8"),
            ("Київська область", "9"),
            ("Кіровоградська область", "10"),
            ("Луганська область", "11"),
            ("Львівська область", "12"),
            ("Миколаївська область", "13"),
            ("Одеська область", "14"),
            ("Полтавська область", "15"),
            ("Рівненська область", "16"),
            ("Сумська область", "17"),
            ("Тернопільська область", "18"),
            ("Харківська область", "19"),
            ("Херсонська область", "20"),
            ("Хмельницька область", "21"),
            ("Черкаська область", "22"),
            ("Чернівецька область", "23"),
            ("Чернігівська область", "24"),
            ("м. Київ", "25"),
        ]
        
        for name, uid in regions_data:
            cur.execute("""
                INSERT OR IGNORE INTO regions (name, uid) VALUES (?, ?)
            """, (name, uid))
        
        conn.commit()

def add_or_update_user(user_id: int, username: str = None, full_name: str = None) -> Dict:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, username, full_name, last_seen)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(?, username),
                full_name = COALESCE(?, full_name),
                last_seen = CURRENT_TIMESTAMP
        """, (user_id, username, full_name, username, full_name))
        
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(cur.fetchone())

def get_user(user_id: int) -> Optional[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def update_user_regions(user_id: int, regions: List[str]):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET regions = ? WHERE user_id = ?
        """, (",".join(regions), user_id))

def get_user_regions(user_id: int) -> List[str]:
    user = get_user(user_id)
    if user and user.get("regions"):
        return user["regions"].split(",")
    return []

def update_user_role(user_id: int, role: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))

def get_all_users() -> List[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY last_seen DESC")
        return [dict(row) for row in cur.fetchall()]

def get_users_count() -> int:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM users")
        return cur.fetchone()["count"]

def get_users_by_region(region: str) -> List[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE regions LIKE ?", (f"%{region}%",))
        return [dict(row) for row in cur.fetchall()]

def get_all_regions() -> List[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM regions ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

def update_region_status(uid: str, status: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE regions SET alert_status = ?, last_updated = CURRENT_TIMESTAMP
            WHERE uid = ?
        """, (status, uid))

def get_region_by_name(name: str) -> Optional[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM regions WHERE name = ?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None

def add_shelter(region: str, city: str, address: str, shelter_type: str = "укриття", 
                capacity: int = 0, lat: float = None, lon: float = None, description: str = None):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO shelters (region, city, address, shelter_type, capacity, lat, lon, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (region, city, address, shelter_type, capacity, lat, lon, description))

def get_shelters_by_region(region: str) -> List[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM shelters WHERE region LIKE ?", (f"%{region}%",))
        return [dict(row) for row in cur.fetchall()]

def get_shelters_by_city(city: str) -> List[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM shelters WHERE city LIKE ?", (f"%{city}%",))
        return [dict(row) for row in cur.fetchall()]

def add_broadcast(message: str, sent_by: str, recipients_count: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO broadcast_history (message, sent_by, recipients_count)
            VALUES (?, ?, ?)
        """, (message, sent_by, recipients_count))

def get_broadcast_history() -> List[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM broadcast_history ORDER BY sent_at DESC LIMIT 50")
        return [dict(row) for row in cur.fetchall()]

def add_admin(username: str, password_hash: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO admin_users (username, password_hash)
            VALUES (?, ?)
        """, (username, password_hash))

def get_admin(username: str) -> Optional[Dict]:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin_users WHERE username = ?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None

def seed_shelters():
    shelters_data = [
        ("Київська область", "Київ", "вул. Хрещатик, станція метро 'Хрещатик'", "метро", 5000),
        ("Київська область", "Київ", "вул. Велика Васильківська, станція метро 'Палац Спорту'", "метро", 4000),
        ("Київська область", "Київ", "Майдан Незалежності, станція метро 'Майдан Незалежності'", "метро", 6000),
        ("Харківська область", "Харків", "пл. Свободи, станція метро 'Держпром'", "метро", 3000),
        ("Харківська область", "Харків", "вул. Сумська, станція метро 'Університет'", "метро", 2500),
        ("Дніпропетровська область", "Дніпро", "пр. Дмитра Яворницького, станція метро 'Центральна'", "метро", 2000),
        ("Львівська область", "Львів", "пл. Ринок, підвал ратуші", "підвал", 200),
        ("Одеська область", "Одеса", "вул. Дерибасівська, підвальні приміщення", "підвал", 500),
        ("Сумська область", "Суми", "вул. Соборна, підвал ТЦ", "підвал", 300),
        ("Полтавська область", "Полтава", "вул. Соборності, підвал адмінбудівлі", "підвал", 250),
    ]
    
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM shelters")
        if cur.fetchone()["count"] == 0:
            for region, city, address, shelter_type, capacity in shelters_data:
                add_shelter(region, city, address, shelter_type, capacity)
            print("✅ Додано базові укриття")
