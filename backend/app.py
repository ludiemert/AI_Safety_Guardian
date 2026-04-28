# pylint: disable=no-member
from flask import Flask, render_template, request, send_from_directory
import cv2

# create unique id
# different name for each file
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


# Upload route => Flask received the request
@app.route("/upload", methods=["POST"])
def upload():
    """Receive image, process it, and show result page."""
    file = request.files["image"]

    if not file or file.filename == "":
        return "No file selected"

    # alter file uuid
    # original_path = "data/uploads/original.jpg"
    # result_path = "data/results/result.jpg"

    # Create unique name
    unique_id = str(uuid.uuid4())

    original_path = f"data/uploads/original_{unique_id}.jpg"
    result_path = f"data/results/result_{unique_id}.jpg"
    # uuid = random unique number
    # each image has different name

    file.save(original_path)

    img = cv2.imread(original_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    cv2.imwrite(result_path, edges)

    # return render_template(
    #    "result.html",
    #    original_image="/data/uploads/original.jpg",
    #    result_image="/data/results/result.jpg",
    # )

    return render_template(
        "result.html",
        original_image=f"/data/uploads/original_{unique_id}.jpg",
        result_image=f"/data/results/result_{unique_id}.jpg",
    )


@app.route("/data/<path:filename>")
def data_files(filename):
    return send_from_directory("../data", filename)


# Run server
if __name__ == "__main__":
    app.run(debug=True)
