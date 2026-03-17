import sqlite3
import pandas as pd

conn = sqlite3.connect("chess_analysis.db")

print(pd.read_sql("SELECT COUNT(*) FROM games", conn))
print(pd.read_sql("SELECT COUNT(*) FROM moves", conn))
print(pd.read_sql("SELECT COUNT(*) FROM motifs", conn))