# pylint: disable=no-member

from flask import Flask, render_template, request, send_from_directory, jsonify
from ultralytics import YOLO
import cv2
import uuid
import csv
from datetime import datetime
import os


app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)

model = YOLO("yolov8n.pt")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["image"]

    if not file or file.filename == "":
        return "No file selected"

    unique_id = str(uuid.uuid4())

    original_path = f"data/uploads/original_{unique_id}.jpg"
    result_path = f"data/results/result_{unique_id}.jpg"

    file.save(original_path)

    img = cv2.imread(original_path)

    results = model(img)
    detections = results[0].boxes

    person_detected = False

    for box in detections:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]

        if class_name == "person":
            person_detected = True

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 100, 200)

    cv2.imwrite(result_path, edges)

    edge_count = cv2.countNonZero(edges)

    height, width = edges.shape
    total_pixels = height * width

    edge_percentage = (edge_count / total_pixels) * 100

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

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    risk_type = "Person Detection" if person_detected else "No Person"
    status = "active" if play_alarm else "safe"
    duration = 0

    csv_file = "data/risk_history.csv"
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

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


@app.route("/data/<path:filename>")
def data_files(filename):
    return send_from_directory("../data", filename)


@app.route("/history")
def history():
    csv_file = "data/risk_history.csv"

    rows = []

    if os.path.isfile(csv_file):
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

    return render_template("history.html", rows=rows)


@app.route("/api/stats")
def api_stats():
    csv_file = "data/risk_history.csv"

    active_count = 0
    safe_count = 0
    edge_scores = []
    risks_by_hour = {}

    if os.path.isfile(csv_file):
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

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


if __name__ == "__main__":
    app.run(debug=True)
