# pylint: disable=no-member

from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    jsonify,
    Response,
)
from ultralytics import YOLO
import cv2
import uuid
from datetime import datetime
import time

from config import (
    MODEL_PATH,
    DATA_DIR,
    UPLOADS_DIR,
    RESULTS_DIR,
    SNAPSHOTS_DIR,
    RISK_HISTORY_FILE,
    create_project_folders,
)

# Import the image detection function.
from detect import analyze_image

# Import functions to save and read the risk history.
from database import save_risk_history, read_risk_history

# Import the Pandas dashboard function.
from analytics import build_dashboard_stats

# =========================
# APP CONFIGURATION
# =========================

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)

create_project_folders()

model = YOLO(MODEL_PATH)

last_snapshot_time = 0

camera_risk_status = {
    "status": "safe",
    "risk_type": "No Risk",
    "message": "No camera risk detected.",
}

# =========================
# HOME PAGE
# =========================


@app.route("/")
def home():
    """Show the home page."""
    return render_template("index.html")


# =========================
# IMAGE UPLOAD + ANALYSIS
# =========================


@app.route("/upload", methods=["POST"])
def upload():
    """Receive image, process image, save history, and show result page."""

    file = request.files["image"]

    if not file or file.filename == "":
        return "No file selected"

    unique_id = str(uuid.uuid4())

    original_path = UPLOADS_DIR / f"original_{unique_id}.jpg"
    result_path = RESULTS_DIR / f"result_{unique_id}.jpg"

    file.save(original_path)

    detection_result = analyze_image(original_path, result_path, model)

    person_detected = detection_result["person_detected"]
    cell_phone_detected = detection_result["cell_phone_detected"]
    person_count = detection_result["person_count"]
    detected_objects_text = detection_result["detected_objects_text"]
    average_confidence = detection_result["average_confidence"]
    edge_percentage = detection_result["edge_percentage"]

    # MVP safety rule:
    # Cell phone in the work area is a high risk.
    # Person without cell phone is only an observation.
    if cell_phone_detected:
        safety_status = "High risk detected"
        risk_level = "High"
        safety_message = "Cell phone detected in the work area."
        play_alarm = True
    elif person_detected:
        safety_status = "Person detected"
        risk_level = "Observation"
        safety_message = "Person detected. No high risk confirmed."
        play_alarm = False
    else:
        safety_status = "Safe"
        risk_level = "Low"
        safety_message = "No risk found."
        play_alarm = False

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    if cell_phone_detected:
        risk_type = "Cell Phone In Work Area"
    elif person_detected:
        risk_type = "Person In Area"
    else:
        risk_type = "No Risk"

    status = "active" if play_alarm else "safe"
    duration = 0

    row_data = {
        "date": date_str,
        "time": time_str,
        "risk_type": risk_type,
        "risk_level": risk_level,
        "edge_score": round(edge_percentage, 2),
        "status": status,
        "duration": duration,
        "person_count": person_count,
        "average_confidence": round(average_confidence, 2),
        "detected_objects": detected_objects_text,
        "image_path": str(result_path),
    }

    save_risk_history(RISK_HISTORY_FILE, row_data)

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


# =========================
# DATA FILES
# =========================


@app.route("/data/<path:filename>")
def data_files(filename):
    """Show uploaded and processed images."""
    return send_from_directory(DATA_DIR, filename)


# =========================
# HISTORY PAGE
# =========================


@app.route("/history")
def history():
    """Show risk history page."""

    rows = read_risk_history(RISK_HISTORY_FILE)

    return render_template("history.html", rows=rows)


# =========================
# DASHBOARD API
# =========================


@app.route("/api/stats")
def api_stats():
    """Send dashboard data as JSON.
    JavaScript uses this API to build the charts.
    """

    # Build chart data with Pandas.
    stats = build_dashboard_stats(RISK_HISTORY_FILE)

    # Send the data to the frontend as JSON.
    return jsonify(stats)


# =========================
# CAMERA PAGE
# =========================


@app.route("/camera")
def camera_page():
    """Show camera page."""
    return render_template("camera.html")


@app.route("/api/camera-status")
def camera_status():
    """Send the current camera risk status as JSON.

    JavaScript uses this API to start or stop the alarm.
    """

    return jsonify(camera_risk_status)


@app.route("/video_feed")
def video_feed():
    """Send webcam video stream."""
    return Response(
        generate_camera_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# =========================
# LIVE CAMERA + SNAPSHOT
# =========================


def generate_camera_frames():
    """Open webcam, detect risks, save snapshots, and send frames to browser.

    The camera checks each frame with YOLO.
    If it finds a person, it saves a snapshot every 10 seconds.
    If it finds a cell phone, it saves a high risk event.
    """

    global last_snapshot_time, camera_risk_status

    camera = cv2.VideoCapture(0)

    while True:
        success, frame = camera.read()

        if not success:
            break

        # Run YOLO detection on the camera frame.
        results = model(frame)
        detections = results[0].boxes

        # Start camera detection variables.
        person_detected = False
        cell_phone_detected = False
        person_count = 0
        detected_objects = []
        confidence_scores = []

        # Check each object detected by YOLO.
        for box in detections:
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Save useful objects for the history.
            if class_name in ["person", "cell phone"]:
                detected_objects.append(class_name)
                confidence_scores.append(round(confidence, 2))

            # Person detection is an observation in the camera.
            if class_name == "person":
                person_detected = True
                person_count += 1

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

                cv2.putText(
                    frame,
                    f"PERSON {confidence:.2f}",
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 0, 255),
                    1,
                    cv2.LINE_AA,
                )

            # Cell phone detection is a risk in the MVP.
            if class_name == "cell phone":
                cell_phone_detected = True

                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)

                cv2.putText(
                    frame,
                    f"CELL PHONE {confidence:.2f}",
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 0, 255),
                    1,
                    cv2.LINE_AA,
                )

        # Update camera risk status for JavaScript.
        if cell_phone_detected:
            camera_risk_status = {
                "status": "active",
                "risk_type": "Cell Phone In Work Area",
                "message": "Cell phone detected in the camera.",
            }
        else:
            camera_risk_status = {
                "status": "safe",
                "risk_type": "No High Risk",
                "message": "No high risk detected by camera.",
            }
        # Save a snapshot every 10 seconds when a person is detected.
        if person_detected:
            current_time = time.time()

            if current_time - last_snapshot_time > 10:
                now = datetime.now()
                snapshot_name = f"snapshot_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                snapshot_path = SNAPSHOTS_DIR / snapshot_name

                cv2.imwrite(str(snapshot_path), frame)

                # Calculate average confidence for the detected objects.
                average_confidence = 0
                if confidence_scores:
                    average_confidence = sum(confidence_scores) / len(confidence_scores)

                # Create text with all detected objects.
                if detected_objects:
                    detected_objects_text = ", ".join(detected_objects)
                else:
                    detected_objects_text = "None"

                # Cell phone is a high risk.
                if cell_phone_detected:
                    risk_type = "Cell Phone In Work Area"
                    risk_level = "High"
                    status = "active"
                else:
                    risk_type = "Camera Person In Area"
                    risk_level = "Observation"
                    status = "safe"

                # Save camera event in the same history CSV.
                row_data = {
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "risk_type": risk_type,
                    "risk_level": risk_level,
                    "edge_score": 0,
                    "status": status,
                    "duration": 0,
                    "person_count": person_count,
                    "average_confidence": round(average_confidence, 2),
                    "detected_objects": detected_objects_text,
                    "image_path": str(snapshot_path),
                }

                save_risk_history(RISK_HISTORY_FILE, row_data)

                last_snapshot_time = current_time

        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

    camera.release()


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(debug=True)
