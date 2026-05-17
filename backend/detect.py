"""Image detection functions.

This file has the computer vision logic.
It uses YOLO and OpenCV to detect people in images.
"""

import cv2


def analyze_image(image_path, result_path, model):
    """Analyze one image and save the result image.

    The function checks if there is a person in the image.
    It draws a red box around each person.
    It also calculates an edge score with OpenCV.
    """

    # Read the image from the upload folder.
    image = cv2.imread(str(image_path))

    # Run YOLO detection on the image.
    results = model(image)

    # Get the detected boxes from the first result.
    detections = results[0].boxes

    # Start the detection variables.
    person_detected = False
    person_count = 0
    detected_objects = []
    confidence_scores = []

    # Check each detected object.
    for box in detections:
        # Get the class id of the object.
        cls_id = int(box.cls[0])

        # Get the class name, for example "person".
        class_name = model.names[cls_id]

        # Get the confidence score of the detection.
        confidence = float(box.conf[0])

        # Get the box position in the image.
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # For now, the MVP only uses person detection.
        if class_name == "person":
            person_detected = True
            person_count += 1

            # Save object name and confidence.
            detected_objects.append(class_name)
            confidence_scores.append(round(confidence, 2))

            # Draw a red box around the person.
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # Write the label on the image.
            cv2.putText(
                image,
                f"PERSON {confidence:.2f}",
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.30,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )

    # Create text with all detected objects.
    if detected_objects:
        detected_objects_text = ", ".join(detected_objects)
    else:
        detected_objects_text = "None"

    # Calculate the average confidence.
    average_confidence = 0
    if confidence_scores:
        average_confidence = sum(confidence_scores) / len(confidence_scores)

    # Convert the image to grayscale.
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect edges in the image.
    edges = cv2.Canny(gray, 100, 200)

    # Count how many edge pixels exist.
    edge_count = cv2.countNonZero(edges)

    # Get image size.
    height, width = edges.shape
    total_pixels = height * width

    # Calculate the edge percentage.
    edge_percentage = (edge_count / total_pixels) * 100

    # Save the final image with boxes.
    cv2.imwrite(str(result_path), image)

    # Return all values needed by app.py.
    return {
        "person_detected": person_detected,
        "person_count": person_count,
        "detected_objects_text": detected_objects_text,
        "average_confidence": round(average_confidence, 2),
        "edge_percentage": round(edge_percentage, 2),
    }
