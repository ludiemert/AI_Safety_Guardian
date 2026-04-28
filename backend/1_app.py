# This imports Flask (web framework)
from flask import Flask, render_template, request

# This imports OpenCV for image processing
import cv2

# This imports NumPy to work with image data
import numpy as np


# This creates the app
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)


# This is the home page route
@app.route("/")
def home():
    return render_template("index.html")


# This route receives the uploaded image
@app.route("/upload", methods=["POST"])
def upload():
    # Get the image file from the form
    file = request.files["image"]

    # If no file is selected, show a message
    if not file:
        return "No file selected"

    # Read the image file as bytes
    file_bytes = np.frombuffer(file.read(), np.uint8)

    # Convert bytes to an OpenCV image
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Convert the image to gray color
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect edges in the image
    edges = cv2.Canny(gray, 100, 200)

    # Save the processed image
    cv2.imwrite("data/result.jpg", edges)

    # Show success message
    return "Image processed! Check data/result.jpg"


# This runs the server
if __name__ == "__main__":
    app.run(debug=True)
