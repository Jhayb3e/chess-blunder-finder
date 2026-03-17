import sqlite3

conn = sqlite3.connect("chess_analysis.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE games (
    game_id TEXT PRIMARY KEY,
    username TEXT,
    date TEXT,
    event TEXT,
    time_control TEXT,
    white TEXT,
    black TEXT,
    result TEXT,
    you_are TEXT,
    opponent TEXT
)
""")

cursor.execute("""
CREATE TABLE moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT,
    move_number INTEGER,
    player TEXT,
    piece TEXT,
    phase TEXT,
    error_type TEXT,
    move_san TEXT
)
""")

cursor.execute("""
CREATE TABLE motifs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT,
    move_number INTEGER,
    motif_type TEXT,
    executed_or_missed TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully.")