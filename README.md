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