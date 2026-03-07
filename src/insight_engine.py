import os
import json
from datetime import datetime
from collections import Counter
import pandas as pd


WEIGHTS = {
    ("Opening", "Blunder", "Fork"): 3,
    ("Middlegame", "Missed Pin", None): 2,
    ("Endgame", "Blunder", "Trap"): 4,
}


def _split_motifs(x):
    if x is None:
        return []
    s = str(x).strip()
    if not s:
        return []
    return [m.strip() for m in s.split(",") if m.strip()]


def get_weight(phase, error_type, motif):
    return WEIGHTS.get((phase, error_type, motif), 1)


def summarize_patterns(df: pd.DataFrame) -> Counter:
    scores = Counter()

    for _, row in df.iterrows():

        phase = row.get("Phase", "")
        error_type = row.get("ErrorType", "")

        detected = _split_motifs(row.get("Detected_Motifs", ""))
        missed = _split_motifs(row.get("Missed_Motif", ""))

        missed_labeled = [f"Missed {m}" for m in missed]

        motifs = detected + missed_labeled

        if not motifs:
            motifs = [None]

        for motif in motifs:

            base_motif = motif if (motif is None or not str(motif).startswith("Missed ")) else None

            scores[(phase, error_type, motif)] += get_weight(phase, error_type, base_motif)

    return scores


def generate_insights(df: pd.DataFrame) -> dict:

    game_count = df["GameID"].nunique() if "GameID" in df.columns else 0

    warning = None

    if game_count < 10:
        warning = "Very small sample size — insights may be unreliable."

    elif game_count < 20:
        warning = "Small sample size — patterns may change with more games."

    scores = summarize_patterns(df)

    top = scores.most_common(10)

    insights = []

    for (phase, error_type, motif), score in top:

        if motif:
            insights.append(
                f"You often {error_type.lower()} in the {phase.lower()} with {str(motif).lower()}."
            )

        else:
            insights.append(
                f"You often {error_type.lower()} in the {phase.lower()}."
            )

    payload = {
        "game_count": int(game_count) if game_count else None,
        "warning": warning,
        "top_patterns": [
            {"phase": p, "error_type": e, "motif": m, "score": s}
            for (p, e, m), s in top
        ],
        "insights": insights,
    }

    return payload


def save_insights(payload: dict, username: str) -> dict:

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    out_dir = os.path.join("data", "insights", username)

    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, f"{username}_insights_{ts}.csv")

    pd.DataFrame({"Insight": payload.get("insights", [])}).to_csv(csv_path, index=False)

    json_path = os.path.join(out_dir, f"{username}_insights_{ts}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return {"csv": csv_path, "json": json_path}


def run_from_dataframe(df: pd.DataFrame, username: str) -> dict:

    payload = generate_insights(df)

    paths = save_insights(payload, username=username)

    return {"payload": payload, "paths": paths}