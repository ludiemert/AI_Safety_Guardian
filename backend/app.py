# pylint: disable=no-member

# Import Flask tools
from flask import Flask, render_template, request, send_from_directory

# Import OpenCV for image processing
import cv2

# Import UUID to create unique file names
import uuid

# Import CSV to save history
import csv

# Import datetime to save date and time
from datetime import datetime

# Import os to check if file exists
import os


# Create Flask app
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)


# Home page route
@app.route("/")
def home():
    """Show the home page."""
    return render_template("index.html")


# Upload route
@app.route("/upload", methods=["POST"])
def upload():
    """Receive image, process image, save history, and show result page."""

    # Get image from HTML form
    file = request.files["image"]

    # Check if user selected a file
    if not file or file.filename == "":
        return "No file selected"

    # Create unique ID for this upload
    unique_id = str(uuid.uuid4())

    # Create file paths
    original_path = f"data/uploads/original_{unique_id}.jpg"
    result_path = f"data/results/result_{unique_id}.jpg"

    # Save original image
    file.save(original_path)

    # Read image with OpenCV
    img = cv2.imread(original_path)

    # Convert image to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect edges in the image
    edges = cv2.Canny(gray, 100, 200)

    # Save processed image
    cv2.imwrite(result_path, edges)

    # -------------------------------
    # Risk detection logic
    # -------------------------------

    # Count edge pixels
    edge_count = cv2.countNonZero(edges)

    # Get image size
    height, width = edges.shape
    total_pixels = height * width

    # Calculate edge percentage
    edge_percentage = (edge_count / total_pixels) * 100

    # If edge score is high, show risk and alarm buttons
    if edge_percentage > 20:
        safety_status = "⚠️ Risk detected"
        risk_level = "Medium"
        safety_message = "Please check the area."
        play_alarm = True
    else:
        safety_status = "✅ Safe"
        risk_level = "Low"
        safety_message = "No visible risk found."
        play_alarm = False

    # -------------------------------
    # Save risk history
    # -------------------------------

    # Get current date and time
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # First version risk type
    risk_type = "Edge Detection"

    # Set status
    status = "active" if play_alarm else "safe"

    # First version duration
    duration = 0

    # CSV file path
    csv_file = "data/risk_history.csv"

    # Check if CSV exists
    file_exists = os.path.isfile(csv_file)

    # Save data in CSV
    with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Create header if CSV does not exist
        if not file_exists:
            writer.writerow(
                [
                    "date",
                    "time",
                    "risk_type",
                    "risk_level",
                    "edge_score",
                    "status",
                    "duration",
                    "image_path",
                ]
            )

        # Save one analysis row
        writer.writerow(
            [
                date_str,
                time_str,
                risk_type,
                risk_level,
                round(edge_percentage, 2),
                status,
                duration,
                result_path,
            ]
        )

    # Send data to result.html
    return render_template(
        "result.html",
        original_image=f"/data/uploads/original_{unique_id}.jpg",
        result_image=f"/data/results/result_{unique_id}.jpg",
        safety_status=safety_status,
        risk_level=risk_level,
        safety_message=safety_message,
        edge_percentage=round(edge_percentage, 2),
        play_alarm=play_alarm,
    )


# Show images from data folder
@app.route("/data/<path:filename>")
def data_files(filename):
    """Show uploaded and processed images."""
    return send_from_directory("../data", filename)


# Run server
if __name__ == "__main__":
    app.run(debug=True)
