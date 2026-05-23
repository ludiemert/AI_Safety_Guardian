"""Dashboard analytics with Pandas.

This file reads the risk history CSV.
It uses Pandas to calculate data for the dashboard charts.
"""

import pandas as pd


def build_dashboard_stats(csv_file):
    """Build dashboard statistics from the risk history.

    The function returns data for:
    - risk vs safe chart
    - average edge score
    - risks by hour chart
    """

    # If the CSV does not exist, return empty dashboard data.
    if not csv_file.exists():
        return _empty_dashboard_stats()

    # Read the CSV file with Pandas.
    df = pd.read_csv(csv_file)

    # Normalize column names.
    # This helps Pandas read old and new CSV headers.
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" - métrica opencv", "", regex=False)
        .str.replace(" - média da confiança da ia", "", regex=False)
    )

    # If the CSV is empty, return empty dashboard data.
    if df.empty:
        return _empty_dashboard_stats()

    # Make sure important columns exist.
    if "status" not in df.columns:
        df["status"] = "safe"

    if "time" not in df.columns:
        df["time"] = "00:00:00"

    if "edge_score" not in df.columns:
        df["edge_score"] = 0

    # Count safe and active rows.
    status_counts = df["status"].value_counts()

    active_count = int(status_counts.get("active", 0))
    safe_count = int(status_counts.get("safe", 0))

    # Calculate average edge score.
    df["edge_score"] = pd.to_numeric(df["edge_score"], errors="coerce").fillna(0)
    average_edge_score = round(df["edge_score"].mean(), 2)

    # Create hour column from time text.
    df["hour"] = df["time"].astype(str).str.slice(0, 2)

    # Count active risks by hour.
    active_rows = df[df["status"] == "active"]
    risks_by_hour = active_rows["hour"].value_counts().sort_index()

    return {
        "risk_safe": {
            "labels": ["Risk", "Safe"],
            "values": [active_count, safe_count],
        },
        "average_edge_score": average_edge_score,
        "risks_by_hour": {
            "hours": risks_by_hour.index.tolist(),
            "values": risks_by_hour.astype(int).tolist(),
        },
    }


def _empty_dashboard_stats():
    """Return empty dashboard data.

    This is used when there is no CSV file yet.
    """

    return {
        "risk_safe": {
            "labels": ["Risk", "Safe"],
            "values": [0, 0],
        },
        "average_edge_score": 0,
        "risks_by_hour": {
            "hours": [],
            "values": [],
        },
    }
