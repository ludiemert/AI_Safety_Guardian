# This imports Flask(web framework)
from flask import Flask, render_template

# this creates the app
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)


# this is the home page route
@app.route("/")
def home():
    return render_template("index.html")


# this runs the server
if __name__ == "__main__":
    app.run(debug=True)
