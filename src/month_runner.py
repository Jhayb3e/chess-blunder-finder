import os
import pandas as pd
from typing import List, Tuple

from pgn_fetcher import fetch_chesscom_games_v2
from engine_analysis import analyze_games_with_stockfish
from motif_detector import analyze_motifs
from insight_engine import generate_insights


BASE_OUTPUT = "outputs"


def run_month_pipeline(username: str, year: int, month: int):
    """
    Runs the full pipeline for one month:
    Fetch → Engine Analysis → Motifs → Insights
    """

    print(f"\n===== Running pipeline for {year}-{month:02d} =====")

    # 1 Fetch games
    pgn_paths, metadata_df, _, _ = fetch_chesscom_games_v2(
        username=username,
        months=[(year, month)]
    )

    if len(pgn_paths) == 0:
        print("No games found this month.")
        return None

    pgn_path = pgn_paths[0]

    # 2 Run engine analysis
    analysis_csv, analysis_df = analyze_games_with_stockfish(
        pgn_path=pgn_path,
        username=username
    )

    # 3 Run motif detection
    motifs_df = analyze_motifs(analysis_df)

    # 4 Generate insights
    insights = generate_insights(motifs_df)

    # 5 Save outputs
    output_dir = os.path.join(BASE_OUTPUT, username, str(year), f"{month:02d}")
    os.makedirs(output_dir, exist_ok=True)

    analysis_df.to_csv(os.path.join(output_dir, "engine_analysis.csv"), index=False)
    motifs_df.to_csv(os.path.join(output_dir, "motifs.csv"), index=False)

    insights_df = pd.DataFrame([insights])
    insights_df.to_csv(os.path.join(output_dir, "insights.csv"), index=False)

    print(f"Saved results to {output_dir}")

    return insights


def run_period_pipeline(username: str, months: List[Tuple[int, int]]):
    """
    Runs pipeline for multiple months and aggregates insights.
    """

    all_insights = []

    for year, month in months:
        result = run_month_pipeline(username, year, month)

        if result is not None:
            result["year"] = year
            result["month"] = month
            all_insights.append(result)

    if len(all_insights) == 0:
        print("No data to summarize.")
        return None

    insights_df = pd.DataFrame(all_insights)

    summary = {
        "total_months": len(insights_df),
        "avg_blunders": insights_df["blunders"].mean() if "blunders" in insights_df else None,
        "avg_mistakes": insights_df["mistakes"].mean() if "mistakes" in insights_df else None,
    }

    return insights_df, summary