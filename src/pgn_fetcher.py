import requests
import os
import io
import chess.pgn
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any

BASE_GAMES_DIR = "games"
METADATA_DIR = os.path.join("data", "metadata")
ARCHIVE_URL_TEMPLATE = "https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"

GAME_TYPES = ["Bullet", "Blitz", "Rapid", "Daily"]


def parse_time_control(tc: str) -> Dict[str, Any]:
    """
    Chess.com TimeControl is usually:
      - "base+inc" in seconds (e.g., "600+0")
      - or "base" in seconds
      - or "-" / "" / weird formats
    Returns base_sec, inc_sec, and a friendly label (e.g., "10+0", "15+10").
    """
    tc = str(tc).strip().replace('"', '')
    base_sec, inc_sec = None, None

    try:
        if "+" in tc:
            base_sec, inc_sec = map(int, tc.split("+"))
        else:
            base_sec = int(tc)
            inc_sec = 0

        base_min = base_sec // 60
        label = f"{base_min}+{inc_sec}"
        return {"base_sec": base_sec, "inc_sec": inc_sec, "label": label}
    except Exception:
        return {"base_sec": None, "inc_sec": None, "label": f"Unknown ({tc})"}


def convert_time_control_to_type(tc: str) -> str:
    """
    Classify into Bullet/Blitz/Rapid/Daily using base minutes.
    """
    info = parse_time_control(tc)
    base_sec = info["base_sec"]
    if base_sec is None:
        return "Unknown"

    minutes = base_sec // 60
    if minutes < 3:
        return "Bullet"
    elif minutes <= 5:
        return "Blitz"
    elif minutes <= 30:
        return "Rapid"
    else:
        return "Daily"


def fetch_chesscom_games_v2(
    username: str,
    months: List[Tuple[int, int]],
    save_games_dir: Optional[str] = None,
    save_metadata_dir: Optional[str] = None,
    timeout: int = 30
) -> Tuple[List[str], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      - pgn_paths: list of saved monthly pgn files
      - metadata_df: row per game
      - monthly_summary_df: row per month with counts by GameType + total
      - month_status_df: row per month with request status for debugging
    """
    username = username.strip().lower()
    save_games_dir = save_games_dir or os.path.join(BASE_GAMES_DIR, username)
    save_metadata_dir = save_metadata_dir or METADATA_DIR
    os.makedirs(save_games_dir, exist_ok=True)
    os.makedirs(save_metadata_dir, exist_ok=True)

    all_metadata = []
    pgn_paths = []
    game_id_counter = 1

    month_status_rows = []
    monthly_summary_rows = []

    for year, month in months:
        url = ARCHIVE_URL_TEMPLATE.format(username=username, year=year, month=month)
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
        except Exception as e:
            month_status_rows.append({
                "Year": year, "Month": month, "URL": url,
                "StatusCode": None, "GamesReturned": 0,
                "Message": f"Request error: {e}"
            })
            # still add a zero summary row
            monthly_summary_rows.append({
                "Year": year, "Month": month, "TotalGames": 0,
                **{gt: 0 for gt in GAME_TYPES},
                "Note": "Request error"
            })
            continue

        if response.status_code != 200:
            # Chess.com often uses 404 when there is no archive for that month
            month_status_rows.append({
                "Year": year, "Month": month, "URL": url,
                "StatusCode": response.status_code, "GamesReturned": 0,
                "Message": "No archive (likely 404) or request blocked"
            })
            monthly_summary_rows.append({
                "Year": year, "Month": month, "TotalGames": 0,
                **{gt: 0 for gt in GAME_TYPES},
                "Note": f"HTTP {response.status_code}"
            })
            continue

        data = response.json()
        games = data.get("games", []) or []

        month_status_rows.append({
            "Year": year, "Month": month, "URL": url,
            "StatusCode": response.status_code, "GamesReturned": len(games),
            "Message": "OK"
        })

        # Build monthly counts by type (even if zero)
        counts = {gt: 0 for gt in GAME_TYPES}

        if not games:
            monthly_summary_rows.append({
                "Year": year, "Month": month, "TotalGames": 0,
                **counts,
                "Note": "No games played this month"
            })
            continue

        # Save PGN for the month
        pgn_path = os.path.join(save_games_dir, f"{year}-{month:02d}.pgn")
        with open(pgn_path, "w", encoding="utf-8") as f:
            for g in games:
                if "pgn" in g:
                    f.write(g["pgn"] + "\n\n")
        pgn_paths.append(pgn_path)

        # Extract metadata per game
        for g in games:
            pgn_text = g.get("pgn", "")
            if not pgn_text:
                continue

            game_obj = chess.pgn.read_game(io.StringIO(pgn_text))
            if game_obj is None:
                continue

            h = game_obj.headers
            white = h.get("White", "")
            black = h.get("Black", "")
            result = h.get("Result", "")
            time_control = h.get("TimeControl", "")
            event = h.get("Event", "")
            date_str = h.get("UTCDate", h.get("Date", "????.??.??"))
            date = date_str.replace(".", "-")

            tc_info = parse_time_control(time_control)
            game_type = convert_time_control_to_type(time_control)
            if game_type in counts:
                counts[game_type] += 1

            if username == white.lower():
                you_are = "White"
                opponent = black
            elif username == black.lower():
                you_are = "Black"
                opponent = white
            else:
                you_are = "Unknown"
                opponent = "Unknown"

            all_metadata.append({
                "GameID": game_id_counter,
                "Username": username,
                "Year": year,
                "Month": month,
                "Date": date,
                "Event": event,
                "TimeControl": time_control,             # raw, e.g. "900+10"
                "TimeControlLabel": tc_info["label"],    # e.g. "15+10"
                "BaseSeconds": tc_info["base_sec"],
                "IncrementSeconds": tc_info["inc_sec"],
                "GameType": game_type,                   # Bullet/Blitz/Rapid/Daily/Unknown
                "White": white,
                "Black": black,
                "Result": result,
                "YouAre": you_are,
                "Opponent": opponent
            })
            game_id_counter += 1

        monthly_summary_rows.append({
            "Year": year,
            "Month": month,
            "TotalGames": len(games),
            **counts,
            "Note": ""
        })

    metadata_df = pd.DataFrame(all_metadata)
    monthly_summary_df = pd.DataFrame(monthly_summary_rows)
    month_status_df = pd.DataFrame(month_status_rows)

    # Save combined metadata (even if empty, to help debugging)
    range_label = f"{months[0][0]}-{months[0][1]:02d}_to_{months[-1][0]}-{months[-1][1]:02d}"
    metadata_csv_path = os.path.join(save_metadata_dir, f"{username}_{range_label}_metadata.csv")
    metadata_df.to_csv(metadata_csv_path, index=False)

    summary_csv_path = os.path.join(save_metadata_dir, f"{username}_{range_label}_monthly_summary.csv")
    monthly_summary_df.to_csv(summary_csv_path, index=False)

    status_csv_path = os.path.join(save_metadata_dir, f"{username}_{range_label}_month_status.csv")
    month_status_df.to_csv(status_csv_path, index=False)

    return pgn_paths, metadata_df, monthly_summary_df, month_status_df