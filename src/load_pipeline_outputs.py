import pandas as pd
import sqlite3
import glob

DB = "chess_analysis.db"

conn = sqlite3.connect(DB)
cursor = conn.cursor()

files = glob.glob("outputs/jaybee024/2025/*/engine_analysis.csv")

for file in files:

    df = pd.read_csv(file)

    # -----------------------------
    # INSERT GAMES (deduplicated)
    # -----------------------------

    games = df[[
        "GameID","Username","Date","Event","TimeControl",
        "White","Black","Result","YouAre","Opponent"
    ]].drop_duplicates(subset=["GameID"])

    games.columns = [
        "game_id","username","date","event","time_control",
        "white","black","result","you_are","opponent"
    ]

    for _, row in games.iterrows():
        cursor.execute("""
        INSERT OR IGNORE INTO games
        (game_id, username, date, event, time_control,
        white, black, result, you_are, opponent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(row))

    # -----------------------------
    # INSERT MOVES
    # -----------------------------

    moves = df[
        ["GameID","MoveNumber","Player","Piece","Phase","ErrorType","MoveSAN"]
    ].copy()

    moves.columns = [
        "game_id","move_number","player","piece","phase","error_type","move_san"
    ]

    moves = moves.dropna(subset=["move_number"])

    moves.to_sql("moves", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print("Games and moves loaded successfully.")