# AI Safety Guardian

AI Safety Guardian is an AI-powered computer vision web app for workplace safety monitoring.

The app uses YOLO, OpenCV, Flask, Pandas and JavaScript to detect people and cell phone risks, save snapshots, store risk history and show dashboard analytics.

## Project Goal

The goal of this project is to simulate a workplace safety monitoring system.

The system can:

- detect people in images
- detect cell phones in images
- run live camera detection
- save automatic snapshots
- save risk history in CSV
- show dashboard charts
- play alarm sounds

Simple English:

> This app checks images and live camera video.
> It detects people and cell phones.
> If it finds a cell phone in the work area, it creates a high risk alert.
> The app saves the history and shows charts.

## Technologies

- Python
- Flask
- YOLO
- OpenCV
- Pandas
- Plotly.js
- JavaScript
- HTML
- CSS
- Git and GitHub

## Main Features

### Image Detection

The user can upload an image.
The app runs YOLO detection and shows the result image with boxes.

### Live Camera Detection

The app can use the notebook webcam.
It detects people and cell phones in real time.

### Risk Alert

If the app detects a cell phone in the work area, it creates a high risk event.

### Automatic Snapshots

When the camera detects a person, the app saves a snapshot every 10 seconds.

### Risk History

The app saves detection records in a CSV file.

### Dashboard Analytics

The dashboard uses Pandas and Plotly.js to show:

- Risk vs Safe
- Average Edge Score
- Risks by Hour

## Detection Rules

Current version:

```text
Person detected -> Observation
Cell phone detected -> High Risk
No person or phone -> Safe

Project Architecture

backend/
  app.py          -> Flask routes and web flow
  config.py       -> project settings and file paths
  detect.py       -> YOLO and OpenCV image detection
  database.py     -> save and read risk history
  analytics.py    -> Pandas dashboard data

frontend/
  templates/      -> HTML pages
  static/         -> CSS, JavaScript and favicon

data/
  uploads/        -> uploaded images
  results/        -> processed images
  snapshots/      -> camera snapshots

How To Run
1. Clone the repository

git clone https://github.com/ludiemert/AI_Safety_Guardian.git
cd AI_Safety_Guardian

2. Create and activate virtual environment
Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

3. Install dependencies
pip install -r requirements.txt

4. Run the app
python backend/app.py

Open in the browser:
http://127.0.0.1:5000