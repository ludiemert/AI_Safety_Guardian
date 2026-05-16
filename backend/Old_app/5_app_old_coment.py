# pylint: disable=no-member

# =========================
# IMPORT LIBRARIES
# =========================

# Import Flask tools
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    jsonify,
    Response,
)

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

# Import time for snapshot cooldown
import time

# =========================
# APP CONFIGURATION
# =========================

# Create Flask app
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)

# Load YOLO model
model = YOLO("yolov8n.pt")

# Store last snapshot time
last_snapshot_time = 0


# =========================
# HOME PAGE
# =========================


# Home page route
@app.route("/")
def home():
    """Show the home page."""

    # Render home page
    return render_template("index.html")


# =========================
# IMAGE UPLOAD + ANALYSIS
# =========================


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

            # Set person detected flag
            person_detected = True

            # Increase person counter
            person_count += 1

            # Save detected object name
            detected_objects.append(class_name)

            # Save confidence score
            confidence_scores.append(round(confidence, 2))

            # Draw red rectangle
            cv2.rectangle(
                img,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                2,
            )

            # Draw label above box
            cv2.putText(
                img,
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

    # Check if confidence list is not empty
    if confidence_scores:

        # Calculate average confidence
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

    # Calculate total pixels
    total_pixels = height * width

    # Calculate edge percentage
    edge_percentage = (edge_count / total_pixels) * 100

    # YOLO risk logic
    if person_detected:

        # Safety status
        safety_status = "👤 Person detected"

        # Risk level
        risk_level = "Observation"

        # Safety message
        safety_message = "Person detected. No risk confirmed yet."

        # Alarm status
        play_alarm = False

    else:

        # Safety status
        safety_status = "✅ No person detected"

        # Risk level
        risk_level = "Low"

        # Safety message
        safety_message = "No risk found."

        # Alarm status
        play_alarm = False

    # Get current date and time
    now = datetime.now()

    # Format date
    date_str = now.strftime("%Y-%m-%d")

    # Format time
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
    with open(
        csv_file,
        mode="a",
        newline="",
        encoding="utf-8",
    ) as file:

        # Create CSV writer
        writer = csv.writer(file)

        # Create header if CSV does not exist
        if not file_exists:

            # Create CSV columns
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

    # Send data to result.html
    return render_template(
        "result.html",
        # Original image
        original_image=(f"/data/uploads/original_{unique_id}.jpg"),
        # Result image
        result_image=(f"/data/results/result_{unique_id}.jpg"),
        # Safety status
        safety_status=safety_status,
        # Risk level
        risk_level=risk_level,
        # Safety message
        safety_message=safety_message,
        # Edge score
        edge_percentage=round(edge_percentage, 2),
        # Alarm status
        play_alarm=play_alarm,
        # Person count
        person_count=person_count,
    )


# =========================
# DATA FILES
# =========================


# Show images from data folder
@app.route("/data/<path:filename>")
def data_files(filename):
    """Show uploaded and processed images."""

    # Return requested file
    return send_from_directory("../data", filename)


# =========================
# HISTORY PAGE
# =========================


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

        # Open CSV file
        with open(
            csv_file,
            mode="r",
            encoding="utf-8",
        ) as file:

            # Read CSV
            reader = csv.reader(file)

            # Convert CSV to list
            rows = list(reader)

    # Send data to HTML page
    return render_template(
        "history.html",
        rows=rows,
    )


# =========================
# DASHBOARD API
# =========================


# API route for chart data
@app.route("/api/stats")
def api_stats():
    """Send chart data as JSON."""

    # CSV file path
    csv_file = "data/risk_history.csv"

    # Risk counter
    active_count = 0

    # Safe counter
    safe_count = 0

    # Edge score list
    edge_scores = []

    # Risks by hour dictionary
    risks_by_hour = {}

    # Read CSV if exists
    if os.path.isfile(csv_file):

        # Open CSV file
        with open(
            csv_file,
            mode="r",
            encoding="utf-8",
        ) as file:

            # Read CSV as dictionary
            reader = csv.DictReader(file)

            # Read each row
            for row in reader:

                # Get status
                status = row.get("status", "safe")

                # Get hour
                hour = row.get("time", "00:00")[:2]

                # Get edge score
                edge_score = float(row.get("edge_score", 0))

                # Count active risks
                if status == "active":

                    # Increase risk count
                    active_count += 1

                    # Count risks by hour
                    risks_by_hour[hour] = risks_by_hour.get(hour, 0) + 1

                # Count safe events
                elif status == "safe":

                    # Increase safe count
                    safe_count += 1

                # Save edge score
                edge_scores.append(edge_score)

    # Calculate average edge score
    average_edge_score = 0

    # Check if list is not empty
    if edge_scores:

        # Calculate average
        average_edge_score = sum(edge_scores) / len(edge_scores)

    # Send data to frontend
    return jsonify(
        {
            "risk_safe": {
                "labels": ["Risk", "Safe"],
                "values": [
                    active_count,
                    safe_count,
                ],
            },
            "average_edge_score": round(
                average_edge_score,
                2,
            ),
            "risks_by_hour": {
                "hours": list(risks_by_hour.keys()),
                "values": list(risks_by_hour.values()),
            },
        }
    )


# =========================
# CAMERA PAGE
# =========================


# Camera page route
@app.route("/camera")
def camera_page():
    """Show camera page."""

    # Render camera page
    return render_template("camera.html")


# =========================
# VIDEO STREAM
# =========================


# Video stream route
@app.route("/video_feed")
def video_feed():
    """Send webcam video stream."""

    # Return video stream
    return Response(
        generate_camera_frames(),
        # Stream type
        mimetype=("multipart/x-mixed-replace; boundary=frame"),
    )


# =========================
# LIVE CAMERA + SNAPSHOT
# =========================


# Generate webcam frames
def generate_camera_frames():
    """Open webcam, detect persons, save snapshots, and send frames."""

    # Use global snapshot timer
    global last_snapshot_time

    # Open webcam
    camera = cv2.VideoCapture(0)

    # Infinite loop
    while True:

        # Read frame from camera
        success, frame = camera.read()

        # If camera fails
        if not success:
            break

        # Run YOLO detection
        results = model(frame)

        # Get detected boxes
        detections = results[0].boxes

        # Person detection flag
        person_detected = False

        # Check detected objects
        for box in detections:

            # Get class ID
            cls_id = int(box.cls[0])

            # Get class name
            class_name = model.names[cls_id]

            # Get confidence score
            confidence = float(box.conf[0])

            # Get box coordinates
            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0],
            )

            # Draw only person boxes
            if class_name == "person":

                # Set detection flag
                person_detected = True

                # Draw rectangle
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    2,
                )

                # Draw label
                cv2.putText(
                    frame,
                    f"P {confidence:.2f}",
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 0, 255),
                    1,
                    cv2.LINE_AA,
                )

        # Save snapshot if person detected
        if person_detected:

            # Get current time
            current_time = time.time()

            # Save snapshot every 10 seconds
            if current_time - last_snapshot_time > 10:

                # Create snapshot name
                snapshot_name = (
                    f"snapshot_" f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                )

                # Snapshot path
                snapshot_path = f"data/snapshots/{snapshot_name}"

                # Save snapshot image
                cv2.imwrite(
                    snapshot_path,
                    frame,
                )

                # Update snapshot timer
                last_snapshot_time = current_time

        # Convert frame to jpg
        _, buffer = cv2.imencode(
            ".jpg",
            frame,
        )

        # Convert jpg to bytes
        frame_bytes = buffer.tobytes()

        # Send frame to browser
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

    # Release camera
    camera.release()


# =========================
# RUN SERVER
# =========================

# Run Flask server
if __name__ == "__main__":

    # Start Flask app
    app.run(debug=True)
