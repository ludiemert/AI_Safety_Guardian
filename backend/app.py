# pylint: disable=no-member

# Import Flask and tools
from flask import Flask, render_template, request, send_from_directory

# Import OpenCV for image processing
import cv2

# Import UUID to create unique file names
import uuid


# Create app
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)


# Home page
@app.route("/")
def home():
    """Show the home page."""
    return render_template("index.html")


# Upload route (receive image)
@app.route("/upload", methods=["POST"])
def upload():
    """Receive image, process it, and show result page."""

    # Get file from form
    file = request.files["image"]

    # Check if file exists
    if not file or file.filename == "":
        return "No file selected"

    # Create unique ID
    unique_id = str(uuid.uuid4())
    # Meaning (A2): create different name for each image

    # Define paths
    original_path = f"data/uploads/original_{unique_id}.jpg"
    result_path = f"data/results/result_{unique_id}.jpg"

    # Save original image
    file.save(original_path)

    # Read image with OpenCV
    img = cv2.imread(original_path)

    # Convert image to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect edges
    edges = cv2.Canny(gray, 100, 200)

    # Save processed image
    cv2.imwrite(result_path, edges)

    # ===============================
    # 🔥 RISK DETECTION LOGIC
    # ===============================

    # Count white pixels (edges)
    edge_count = cv2.countNonZero(edges)

    # Get image size
    height, width = edges.shape
    total_pixels = height * width

    # Calculate percentage of edges
    edge_percentage = (edge_count / total_pixels) * 100

    # Simple logic
    if edge_percentage > 20:  # 20% risc
        safety_status = "⚠️ Risk detected"
        risk_level = "Medium"
        safety_message = "Please check the area."
        play_alarm = True
    else:
        safety_status = "✅ Safe"
        risk_level = "Low"
        safety_message = "No visible risk found."
        play_alarm = False

    # ===============================
    # SEND DATA TO HTML
    # ===============================

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


# Route to serve images from data folder
@app.route("/data/<path:filename>")
def data_files(filename):
    return send_from_directory("../data", filename)


# Run server
if __name__ == "__main__":
    app.run(debug=True)
