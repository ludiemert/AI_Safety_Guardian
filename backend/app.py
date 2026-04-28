from flask import Flask, render_template, request, send_from_directory
import cv2
import numpy as np

# Create app
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Upload route
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["image"]

    if not file or file.filename == "":
        return "No file selected"

    original_path = "data/uploads/original.jpg"
    result_path = "data/results/result.jpg"

    file.save(original_path)

    img = cv2.imread(original_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    cv2.imwrite(result_path, edges)

    return render_template(
        "result.html",
        original_image="/data/uploads/original.jpg",
        result_image="/data/results/result.jpg",
    )


@app.route("/data/<path:filename>")
def data_files(filename):
    return send_from_directory("../data", filename)


# Run server
if __name__ == "__main__":
    app.run(debug=True)
