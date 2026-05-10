# pylint: disable=no-member

# Import Flask tools
from flask import Flask, render_template, request, send_from_directory, jsonify

# Import YOLO model
from ultralytics import YOLO

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

# Load YOLO model
model = YOLO("yolov8n.pt")


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

    # Create unique ID
    unique_id = str(uuid.uuid4())

    # Create file paths
    original_path = f"data/uploads/original_{unique_id}.jpg"
    result_path = f"data/results/result_{unique_id}.jpg"

    # Save original image
    file.save(original_path)

    # Read image with OpenCV
    img = cv2.imread(original_path)

    # Run YOLO detection
    results = model(img)

    # Get detected boxes
    detections = results[0].boxes

    # Person detection flag
    person_detected = False

    # Check detected objects
    for box in detections:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]

        if class_name == "person":
            person_detected = True

    # Convert image to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect edges
    edges = cv2.Canny(gray, 100, 200)

    # Save processed image
    cv2.imwrite(result_path, edges)

    # Count edge pixels
    edge_count = cv2.countNonZero(edges)

    # Get image size
    height, width = edges.shape
    total_pixels = height * width

    # Calculate edge percentage
    edge_percentage = (edge_count / total_pixels) * 100

    # YOLO risk logic
    if person_detected:
        safety_status = "👤 Person detected"
        risk_level = "Observation"
        safety_message = "Person detected. No risk confirmed yet."
        play_alarm = False
    else:
        safety_status = "✅ No person detected"
        risk_level = "Low"
        safety_message = "No risk found."
        play_alarm = False

    # Get current date and time
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Risk type
    risk_type = "Person Detection" if person_detected else "No Person"

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

        # Save one row
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


# History page route
@app.route("/history")
def history():
    """Show risk history page."""

    # CSV file path
    csv_file = "data/risk_history.csv"

    # Create empty list
    rows = []

    # Read CSV file if exists
    if os.path.isfile(csv_file):
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

    # Send data to HTML page
    return render_template("history.html", rows=rows)


# API route for chart data
@app.route("/api/stats")
def api_stats():
    """Send chart data as JSON."""

    # CSV file path
    csv_file = "data/risk_history.csv"

    # Counters
    active_count = 0
    safe_count = 0

    # Edge score list
    edge_scores = []

    # Risks by hour
    risks_by_hour = {}

    # Read CSV if exists
    if os.path.isfile(csv_file):
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            # Read each row
            for row in reader:
                status = row["status"]
                hour = row["time"][:2]
                edge_score = float(row["edge_score"])

                if status == "active":
                    active_count += 1
                    risks_by_hour[hour] = risks_by_hour.get(hour, 0) + 1
                elif status == "safe":
                    safe_count += 1

                edge_scores.append(edge_score)

    # Calculate average edge score
    average_edge_score = 0
    if edge_scores:
        average_edge_score = sum(edge_scores) / len(edge_scores)

    # Send data to frontend
    return jsonify(
        {
            "risk_safe": {
                "labels": ["Risk", "Safe"],
                "values": [active_count, safe_count],
            },
            "average_edge_score": round(average_edge_score, 2),
            "risks_by_hour": {
                "hours": list(risks_by_hour.keys()),
                "values": list(risks_by_hour.values()),
            },
        }
    )


# Run server
if __name__ == "__main__":
    app.run(debug=True)
