# upgraded_tactical_motif.py
from pathlib import Path
import pandas as pd
import chess
import chess.engine
import os
from datetime import datetime

# === CONFIGURATION ===
INPUT_FILE = "data/deep_analysis/user_start_end_deep_analysis.csv"
OUTPUT_FILE = "data/tactical_motifs_upgraded.csv"
DEFAULT_ENGINE = Path(__file__).resolve().parents[1] / "stockfish.exe"
STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", str(DEFAULT_ENGINE))
STOCKFISH_DEPTH = 15  # can adjust

os.makedirs("data", exist_ok=True)

# --- Motif detection functions ---
def detect_fork(board):
    attacker_color = board.turn
    for move in board.legal_moves:
        temp_board = board.copy(stack=False)
        temp_board.push(move)
        attacked_squares = list(temp_board.attacks(move.to_square))
        valuable_targets = [sq for sq in attacked_squares
                            if temp_board.piece_at(sq) and temp_board.piece_at(sq).color != attacker_color]
        if len(valuable_targets) >= 2:
            return True
    return False

def detect_pin(board):
    opponent_color = not board.turn
    for sq in chess.SQUARES:
        if board.is_pinned(opponent_color, sq):
            return True
    return False

def detect_skewer(board):
    attacker_color = board.turn
    opponent_color = not attacker_color
    piece_values = {chess.KING: 10000, chess.QUEEN: 9, chess.ROOK: 5,
                    chess.BISHOP: 3, chess.KNIGHT: 3, chess.PAWN: 1}
    for move in board.legal_moves:
        temp_board = board.copy(stack=False)
        temp_board.push(move)
        for sq in chess.SQUARES:
            piece = temp_board.piece_at(sq)
            if piece and piece.color == opponent_color:
                attackers = temp_board.attackers(attacker_color, sq)
                if attackers:
                    for attacker_sq in attackers:
                        attacker_piece = temp_board.piece_at(attacker_sq)
                        if attacker_piece and attacker_piece.piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP]:
                            ray = chess.SquareSet.ray(attacker_sq, sq)
                            if ray:
                                behind_squares = [s for s in ray if s != sq]
                                for b_sq in behind_squares:
                                    behind_piece = temp_board.piece_at(b_sq)
                                    if behind_piece and behind_piece.color == opponent_color:
                                        if piece_values[piece.piece_type] > piece_values[behind_piece.piece_type]:
                                            return True
    return False

def detect_trap(board):
    attacker_color = board.turn
    for move in board.legal_moves:
        temp_board = board.copy(stack=False)
        temp_board.push(move)
        if not temp_board.is_attacked_by(attacker_color, move.to_square) and \
           temp_board.is_attacked_by(not attacker_color, move.to_square):
            return True
    return False

# --- Main analysis function ---
def analyze_motifs(df):

    detected = []
    missed = []
    missed_moves = []

    for idx, row in df.iterrows():

        fen = row.get("FEN")
        player_color = row.get("Player", "White")

        if not fen:
            detected.append("")
            missed.append("")
            missed_moves.append("")
            continue

        board = chess.Board(fen)

        motifs_found = []

        if detect_fork(board):
            motifs_found.append("Fork")

        if detect_pin(board):
            motifs_found.append("Pin")

        if detect_skewer(board):
            motifs_found.append("Skewer")

        if detect_trap(board):
            motifs_found.append("Trap")

        detected.append(", ".join(motifs_found) if motifs_found else "")
        missed.append("")
        missed_moves.append("")

    df["Detected_Motifs"] = detected
    df["Missed_Motif"] = missed
    df["Missed_Motif_Move"] = missed_moves

    return df

    # --- Create username + dated output folder ---
    username = df["Username"].iloc[0] if "Username" in df.columns else "user"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    output_dir = os.path.join("data", "motifs", username)
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"{username}_tactical_motifs_{timestamp}.csv")
    df.to_csv(output_file, index=False)

    print(f"✅ Motif detection completed. Results saved to {output_file}")
    return df

# --- Entry point ---
def main():
    df = pd.read_csv(INPUT_FILE)
    analyze_motifs(df)

if __name__ == "__main__":
    main()
