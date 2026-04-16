import sqlite3
import pandas as pd

# -------------------------------
# CREATE DATABASE & TABLE
# -------------------------------
def init_db():
    conn = sqlite3.connect("nutrition.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food TEXT,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# -------------------------------
# INSERT DATA
# -------------------------------
def insert_meal(food, calories, protein, fat, carbs):
    conn = sqlite3.connect("nutrition.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO meals (food, calories, protein, fat, carbs)
        VALUES (?, ?, ?, ?, ?)
    """, (food, calories, protein, fat, carbs))

    conn.commit()
    conn.close()


# -------------------------------
# FETCH DATA
# -------------------------------
def get_meals():
    conn = sqlite3.connect("nutrition.db")

    df = pd.read_sql("SELECT * FROM meals ORDER BY date DESC", conn)

    conn.close()
    return df
