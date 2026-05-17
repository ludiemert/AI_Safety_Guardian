"""Risk history storage.

This file saves detection results in a CSV file.
Later, this file can change from CSV to SQLite or PostgreSQL.
"""

import csv

RISK_HISTORY_COLUMNS = [
    "date",
    "time",
    "risk_type",
    "risk_level",
    "edge_score",
    "status",
    "duration",
    "person_count",
    "average_confidence",
    "detected_objects",
    "image_path",
]


def save_risk_history(csv_file, row_data):
    """Save one risk record in the CSV history.

    If the CSV file does not exist, this function creates the header.
    Then it adds one new row with the detection result.
    """

    # Check if the CSV already exists.
    file_exists = csv_file.exists()

    # Open the CSV file in append mode.
    with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Create the header only one time.
        if not file_exists:
            writer.writerow(RISK_HISTORY_COLUMNS)

        # Save one detection record.
        writer.writerow(
            [
                row_data["date"],
                row_data["time"],
                row_data["risk_type"],
                row_data["risk_level"],
                row_data["edge_score"],
                row_data["status"],
                row_data["duration"],
                row_data["person_count"],
                row_data["average_confidence"],
                row_data["detected_objects"],
                row_data["image_path"],
            ]
        )


def read_risk_history(csv_file):
    """Read all rows from the CSV history.

    This function returns the header and all history rows.
    If the CSV does not exist, it returns only the header.
    """

    # If there is no CSV file, return only the columns.
    if not csv_file.exists():
        return [RISK_HISTORY_COLUMNS]

    # Read all rows from the CSV file.
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        return list(reader)


def read_risk_history_as_dicts(csv_file):
    """Read the CSV history as dictionaries.

    This format is useful for charts and API data.
    """

    # If there is no CSV file, return an empty list.
    if not csv_file.exists():
        return []

    # Read each CSV row as a dictionary.
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)
