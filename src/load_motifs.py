import pandas as pd
import sqlite3
import glob

DB = "chess_analysis.db"
conn = sqlite3.connect(DB)

files = glob.glob("outputs/jaybee024/2025/*/motifs.csv")

rows = []

for file in files:

    df = pd.read_csv(file)

    for _, r in df.iterrows():

        detected = str(r["Detected_Motifs"]).strip()
        missed = str(r["Missed_Motif"]).strip()

        if detected and detected.lower() != "nan" and detected != "":
            rows.append((r["GameID"], r["MoveNumber"], detected, "executed"))

        if missed and missed.lower() != "nan" and missed != "":
            rows.append((r["GameID"], r["MoveNumber"], missed, "missed"))

motifs = pd.DataFrame(rows, columns=[
    "game_id","move_number","motif_type","executed_or_missed"
])

motifs.to_sql("motifs", conn, if_exists="append", index=False)

conn.close()

print("Motifs loaded correctly.")