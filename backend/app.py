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

from detect import analyze_image

from database import (
    save_risk_history,
    read_risk_history,
    read_risk_history_as_dicts,
)

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
    person_count = detection_result["person_count"]
    detected_objects_text = detection_result["detected_objects_text"]
    average_confidence = detection_result["average_confidence"]
    edge_percentage = detection_result["edge_percentage"]

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

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    risk_type = "Person Detection" if person_detected else "No Person"
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
    """Send chart data as JSON."""

    active_count = 0
    safe_count = 0
    edge_scores = []
    risks_by_hour = {}

    rows = read_risk_history_as_dicts(RISK_HISTORY_FILE)

    for row in rows:
        status = row.get("status", "safe")
        hour = row.get("time", "00:00")[:2]
        edge_score = float(row.get("edge_score", 0))

        if status == "active":
            active_count += 1
            risks_by_hour[hour] = risks_by_hour.get(hour, 0) + 1

        elif status == "safe":
            safe_count += 1

        edge_scores.append(edge_score)

    average_edge_score = 0
    if edge_scores:
        average_edge_score = sum(edge_scores) / len(edge_scores)

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


# =========================
# CAMERA PAGE
# =========================


@app.route("/camera")
def camera_page():
    """Show camera page."""
    return render_template("camera.html")


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
    """Open webcam, detect persons, save snapshots, and send frames to browser."""

    global last_snapshot_time

    camera = cv2.VideoCapture(0)

    while True:
        success, frame = camera.read()

        if not success:
            break

        results = model(frame)
        detections = results[0].boxes

        person_detected = False

        for box in detections:
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if class_name == "person":
                person_detected = True

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

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

        if person_detected:
            current_time = time.time()

            if current_time - last_snapshot_time > 10:
                snapshot_name = (
                    f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                )

                snapshot_path = SNAPSHOTS_DIR / snapshot_name

                cv2.imwrite(str(snapshot_path), frame)

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
