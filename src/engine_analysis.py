import os
from pathlib import Path
import chess.pgn
from stockfish import Stockfish
import pandas as pd
from datetime import datetime

# --- Configuration ---
DEFAULT_ENGINE = Path(__file__).resolve().parents[1] / "stockfish.exe"
STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", str(DEFAULT_ENGINE))
EVAL_THRESHOLD = {"blunder": 300, "mistake": 200, "inaccuracy": 100}  # centipawns
STOCKFISH_DEPTH = 15


# --- Helper Functions ---
def classify_error(eval_drop):
    if eval_drop >= EVAL_THRESHOLD["blunder"]:
        return "Blunder"
    elif eval_drop >= EVAL_THRESHOLD["mistake"]:
        return "Mistake"
    elif eval_drop >= EVAL_THRESHOLD["inaccuracy"]:
        return "Inaccuracy"
    else:
        return None

def get_game_phase(fullmove_number):
    if fullmove_number <= 10:
        return "Opening"
    elif fullmove_number <= 30:
        return "Middlegame"
    else:
        return "Endgame"

# --- Main function ---
def analyze_games_with_stockfish(folder_path=None, pgn_path=None, username=None, start_date=None, end_date=None):
    username_str = username or "user"
    stockfish = Stockfish(path=STOCKFISH_PATH, depth=STOCKFISH_DEPTH)
    results = []
    total_games = 0

    # --- Determine PGN files to analyze ---
    pgn_files = []

    if pgn_path:
        pgn_files = [pgn_path]

    elif folder_path:
        pgn_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.endswith(".pgn")
        ]

    else:
        raise ValueError("Provide folder_path or pgn_path")

    # --- Loop through PGN files ---
    for pgn_file_path in pgn_files:

        filename = os.path.basename(pgn_file_path)

        with open(pgn_file_path) as pgn_file:
            while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    total_games += 1
                    board = game.board()
                    node = game

                    # --- Progress print: game start ---
                    white = game.headers.get("White", "")
                    black = game.headers.get("Black", "")
                    date_str = game.headers.get("UTCDate", game.headers.get("Date", "????.??.??"))
                    date = date_str.replace(".", "-")
                    print(f"Analyzing game {total_games} ({white} vs {black}, {date})")

                    # Extract PGN headers for metadata
                    headers = game.headers
                    white = headers.get("White", "")
                    black = headers.get("Black", "")
                    result = headers.get("Result", "")
                    time_control = headers.get("TimeControl", "")
                    event = headers.get("Event", "")
                    you_are = "White" if username and username.lower() == white.lower() else "Black" if username and username.lower() == black.lower() else "Unknown"
                    opponent = black if you_are == "White" else white if you_are == "Black" else "Unknown"

                    while not node.is_end():
                        move = node.variation(0).move
                        fen_before = board.fen()
                        stockfish.set_fen_position(fen_before)
                        eval_before = stockfish.get_evaluation()

                        # --- Progress print: move ---
                        MOVE_PROGRESS_INTERVAL = 20
                        if board.fullmove_number % MOVE_PROGRESS_INTERVAL == 0:
                            try:
                                move_san = board.san(move)
                            except:
                                move_san = "?"
                            print(f"  Move {board.fullmove_number}: {move_san} ({'White' if board.turn else 'Black'})")

                        try:
                            move_san = board.san(move)
                        except:
                            move_san = "?"

                        board.push(move)
                        fen_after = board.fen()
                        stockfish.set_fen_position(fen_after)
                        eval_after = stockfish.get_evaluation()

                        # Skip mate evaluations
                        if eval_before["type"] == "mate" or eval_after["type"] == "mate":
                            node = node.variation(0)
                            continue

                        cp_before = eval_before["value"]
                        cp_after = eval_after["value"]
                        drop = cp_before - cp_after

                        if drop > EVAL_THRESHOLD["inaccuracy"]:
                            error_type = classify_error(drop)
                            piece = board.piece_at(move.to_square).symbol() if board.piece_at(move.to_square) else "?"
                            phase = get_game_phase(board.fullmove_number)

                            results.append({
                                "GameID": total_games,
                                "Username": username_str,
                                "Date": date,
                                "Event": event,
                                "TimeControl": time_control,
                                "White": white,
                                "Black": black,
                                "Result": result,
                                "YouAre": you_are,
                                "Opponent": opponent,
                                "MoveNumber": board.fullmove_number,
                                "Player": "White" if board.turn else "Black",
                                "Piece": piece,
                                "FEN": fen_before,
                                "Drop": drop,
                                "ErrorType": error_type,
                                "Phase": phase,
                                "MoveSAN": move_san
                            })

                            # --- Progress print: flagged moves ---
                            FLAGGED_PROGRESS_INTERVAL = 50
                            if len(results) % FLAGGED_PROGRESS_INTERVAL == 0:
                                print(f"  {len(results)} flagged positions so far...")

                        node = node.variation(0)

                    # --- Progress print: end of file ---
                    print(f"Finished analyzing {filename}. Total flagged positions so far: {len(results)}\n")

    if not results:
        print("⚠️ No flagged positions found.")
        return pd.DataFrame()

# --- Save CSV in data/deep_analysis/{username}/ with timestamp ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    user_output_dir = os.path.join("data", "deep_analysis", username_str)
    os.makedirs(user_output_dir, exist_ok=True)

    start_str = start_date.strftime("%Y-%m-%d") if start_date else "start"
    end_str = end_date.strftime("%Y-%m-%d") if end_date else "end"

    output_csv = os.path.join(
        user_output_dir,
        f"{username_str}_{start_str}_{end_str}_{timestamp}_deep_analysis.csv"
    )
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)

    print(f"✅ Deep analysis complete. Games analyzed: {total_games}, flagged positions: {len(results)}")
    print(f"CSV saved to: {output_csv}")

    return output_csv, df


# --- Quick test ---
if __name__ == "__main__":
    folder_path = "games/jaybee024"  # adjust this path
    output_csv, df = analyze_games_with_stockfish(folder_path)
    print(f"Analysis CSV saved as: {output_csv}")
    print(df.head())  # optional: show first few rows
