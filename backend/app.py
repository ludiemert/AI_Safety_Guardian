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

    # Count detected persons
    person_count = 0

    # Store detected objects
    detected_objects = []

    # Store confidence values
    confidence_scores = []

    # Check detected objects
    for box in detections:

        # Get object class ID
        cls_id = int(box.cls[0])

        # Get object name
        class_name = model.names[cls_id]

        # Get confidence score
        confidence = float(box.conf[0])

        # Get box coordinates
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Check if object is person
        if class_name == "person":
            person_detected = True
            person_count += 1

            # Save detected object name
            detected_objects.append(class_name)

            # Save confidence score
            confidence_scores.append(round(confidence, 2))

            # Draw red rectangle
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # Draw small label above box
            cv2.putText(
                img,
                # "PERSON",
                f"PERSON {confidence:.2f}",
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.30,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )

    # Create text for detected objects
    detected_objects_text = ", ".join(detected_objects) if detected_objects else "None"

    # Calculate average confidence
    average_confidence = 0

    if confidence_scores:
        average_confidence = sum(confidence_scores) / len(confidence_scores)

    # Convert image to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect edges
    edges = cv2.Canny(gray, 100, 200)

    # Save image with annotations
    cv2.imwrite(result_path, img)

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
                    "person_count",
                    "average_confidence",
                    "detected_objects",
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
                person_count,
                round(average_confidence, 2),
                detected_objects_text,
                result_path,
            ]
        )
        # Resultado no CSV,  Vai ficar assim: date,time,risk_type,risk_level,edge_score,status,duration,person_count,average_confidence,
        # detected_objects,image_path 2026-05-10,15:40:10,
        # Person Detection,Observation,7.23,safe,0,1,0.89,person,data/results/result_x.jpg

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
        person_count=person_count,
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
                status = row.get("status", "safe")
                hour = row.get("time", "00:00")[:2]
                edge_score = float(row.get("edge_score", 0))

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
