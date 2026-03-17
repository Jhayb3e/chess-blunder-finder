import sqlite3

DATABASE_NAME = "chess_analysis.db"

conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

# Sample games
games = [
("game1","2024-01-10",1600,"blitz","loss",42),
("game2","2024-01-15",1650,"rapid","win",55),
("game3","2024-02-02",1700,"blitz","loss",38)
]

cursor.executemany("""
INSERT OR IGNORE INTO games
(game_id,date,opponent_rating,time_control,result,total_moves)
VALUES (?,?,?,?,?,?)
""", games)

# Sample moves
moves = [
("game1",12,"opening",120,"Blunder"),
("game1",18,"middlegame",60,"Mistake"),
("game2",24,"middlegame",90,"Blunder"),
("game3",30,"endgame",40,"Inaccuracy")
]

cursor.executemany("""
INSERT INTO moves
(game_id,move_number,phase,centipawn_loss,error_type)
VALUES (?,?,?,?,?)
""", moves)

# Sample motifs
motifs = [
("game1",18,"fork","missed"),
("game2",24,"pin","executed"),
("game3",30,"skewer","missed")
]

cursor.executemany("""
INSERT INTO motifs
(game_id,move_number,motif_type,executed_or_missed)
VALUES (?,?,?,?)
""", motifs)

conn.commit()
conn.close()

print("Sample data inserted.")