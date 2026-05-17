"""Project settings and file paths.

This file keeps the main paths of the project in one place.
It makes the app easier to read and easier to change.
"""

from pathlib import Path

# Base folder of the project.
BASE_DIR = Path(__file__).resolve().parents[1]

# YOLO model file.
MODEL_PATH = BASE_DIR / "yolov8n.pt"

# Main data folder.
DATA_DIR = BASE_DIR / "data"

# Folder for uploaded images.
UPLOADS_DIR = DATA_DIR / "uploads"

# Folder for processed result images.
RESULTS_DIR = DATA_DIR / "results"

# Folder for camera snapshots.
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

# CSV file with the risk history.
RISK_HISTORY_FILE = DATA_DIR / "risk_history.csv"

# Image types allowed in upload.
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}


def create_project_folders():
    """Create the folders used by the app.

    The app needs these folders to save uploads,
    result images and camera snapshots.
    """

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
