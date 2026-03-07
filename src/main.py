import streamlit as st
import pandas as pd

from pgn_fetcher import fetch_chesscom_games_v2
from engine_analysis import analyze_games_with_stockfish
from motif_detector import analyze_motifs
from insight_engine import run_from_dataframe
from month_runner import run_month_pipeline, run_period_pipeline


# -----------------------------
# App Configuration
# -----------------------------

st.set_page_config(page_title="Chess Blunder Finder", layout="wide")

st.title("♟️ Chess Blunder Finder")
st.caption("Analyze chess games to uncover recurring mistakes and tactical weaknesses.")


if "deep_df" not in st.session_state:
    st.session_state.deep_df = None

if "motif_df" not in st.session_state:
    st.session_state.motif_df = None


tab = st.sidebar.radio(
    "Navigation",
    ["Game Analysis", "Deep Analysis", "Tactical Motifs", "Insight Builder", "Visualizer"]
)


# ----------------------
# Tab 1: Game Analysis
# ----------------------

if tab == "Game Analysis":

    st.header("Game Analysis Pipeline")

    username = st.text_input("Chess.com Username")

    year = st.number_input(
        "Select Year",
        min_value=2000,
        max_value=2100,
        value=2025
    )

    mode = st.radio(
        "Analysis Mode",
        ["Run Full Year", "Custom Months"]
    )

    if mode == "Custom Months":

        month_map = {
            "Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
            "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12
        }

        selected_month_names = st.multiselect(
            "Select Months",
            list(month_map.keys()),
            default=["Jan"]
        )

        months = [month_map[m] for m in selected_month_names]

    else:

        months = list(range(1,13))


    if st.button("Run Full Pipeline"):

        if username:

            months_list = [(year, m) for m in months]

            with st.spinner("Running full analysis pipeline..."):

                insights_df, summary = run_period_pipeline(username, months_list)

            if insights_df is not None:

                st.success("Analysis complete")

                st.subheader("Monthly Insights")

                if isinstance(insights_df, pd.DataFrame):

                    insights_display = insights_df.copy()

                    # Remove backend columns not meant for UI
                    if "top_patterns" in insights_display.columns:
                        insights_display = insights_display.drop(columns=["top_patterns"])

                    st.dataframe(insights_display)

                else:
                    st.write(insights_df)

                st.subheader("Summary")

                if isinstance(summary, dict):

                    summary_clean = summary.copy()

                    # Remove top_patterns so it doesn't appear in UI
                    if "top_patterns" in summary_clean:
                        summary_clean.pop("top_patterns")

                    st.json(summary_clean)

                else:
                    st.write(summary)

            else:

                st.warning("No games found for the selected months.")

        else:

            st.warning("Please enter a Chess.com username.")


# ----------------------
# Tab 2: Deep Analysis
# ----------------------

elif tab == "Deep Analysis":

    st.header("Stockfish Deep Analysis")

    folder_path = st.text_input(
        "PGN Folder Path",
        value="games/"
    )

    username = st.text_input("Username (optional)")

    if st.button("Run Deep Analysis"):

        if folder_path:

            output_csv, df = analyze_games_with_stockfish(
                folder_path,
                username=username
            )

            st.success(f"Analysis complete. Saved to {output_csv}")

            st.dataframe(df.head())

        else:

            st.warning("Please enter a valid PGN folder path.")


# ----------------------
# Tab 3: Tactical Motifs
# ----------------------

elif tab == "Tactical Motifs":

    st.header("Tactical Motif Detection")

    deep_csv = st.file_uploader(
        "Upload Deep Analysis CSV",
        type=["csv"]
    )

    if st.button("Run Motif Detection") and deep_csv:

        df = pd.read_csv(deep_csv)

        df_motifs = analyze_motifs(df)

        st.success("Motif detection complete")

        st.dataframe(df_motifs.head())

    elif not deep_csv:

        st.info("Upload a deep analysis CSV to detect tactical motifs.")


# ----------------------
# Tab 4: Insight Builder
# ----------------------

elif tab == "Insight Builder":

    st.header("Insight Builder")

    motifs_csv = st.file_uploader(
        "Upload Motif CSV",
        type=["csv"],
        key="motifs_for_insights"
    )

    if st.button("Generate Insights") and motifs_csv:

        df_m = pd.read_csv(motifs_csv)

        username_guess = (
            df_m["Username"].iloc[0]
            if "Username" in df_m.columns
            else "user"
        )

        result = run_from_dataframe(df_m, username=username_guess)

        payload = result["payload"]

        if payload.get("warning"):
            st.warning(payload["warning"])
        else:
            st.success("Insights generated")

        st.subheader("Key Insights")

        insights_list = payload.get("insights", [])

        if isinstance(insights_list, list):

            for text in insights_list:

                text = str(text)

                if "—" in text:
                    text = text.split("—")[0]

                st.write(f"• {text.strip()}")

        else:

            st.write(insights_list)

        st.info(
            f"Saved: {result['paths']['csv']} and {result['paths']['json']}"
        )


# ----------------------
# Tab 5: Visualizer
# ----------------------

elif tab == "Visualizer":

    st.header("Visualizer")

    st.info(
        "Interactive charts and dashboards will appear here in future versions."
    )