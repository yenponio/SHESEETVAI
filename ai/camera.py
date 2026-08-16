import cv2
from ultralytics import YOLO

# Load YOLOv8 Pose model
model = YOLO("yolov8n-pose.pt")

# Confidence threshold
CONF = 0.5

# COCO keypoint names
KEYPOINTS = {
    0: "Nose",
    1: "Left Eye",
    2: "Right Eye",
    3: "Left Ear",
    4: "Right Ear",
    5: "Left Shoulder",
    6: "Right Shoulder",
    7: "Left Elbow",
    8: "Right Elbow",
    9: "Left Wrist",
    10: "Right Wrist",
    11: "Left Hip",
    12: "Right Hip",
    13: "Left Knee",
    14: "Right Knee",
    15: "Left Ankle",
    16: "Right Ankle",
}

# Open webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    results = model.predict(frame, verbose=False)

    annotated = frame.copy()

    if len(results):

        r = results[0]

        # Draw pose
        annotated = r.plot()

        if r.keypoints is not None:

            data = r.keypoints.data.cpu().numpy()

            if len(data):

                # Use the first detected person
                person = data[0]

                body = {}

                # Store all body keypoints
                for idx, kp in enumerate(person):

                    x, y, conf = kp

                    body[KEYPOINTS[idx]] = {
                        "x": float(x),
                        "y": float(y),
                        "conf": float(conf),
                        "visible": conf > CONF
                    }

                # ===============================
                # Inspection Logic
                # ===============================

                inspection = {
                    "student_detected": True,

                    "upper_body_visible": (
                        body["Left Shoulder"]["visible"] and
                        body["Right Shoulder"]["visible"]
                    ),

                    "lower_body_visible": (
                        body["Left Hip"]["visible"] and
                        body["Right Hip"]["visible"] and
                        body["Left Knee"]["visible"] and
                        body["Right Knee"]["visible"]
                    )
                }

                # ===============================
                # Display Results
                # ===============================

                y_text = 30

                cv2.putText(
                    annotated,
                    "AI Dress Code Inspection",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )

                y_text += 40

                checks = [
                    ("Student Detected", inspection["student_detected"]),
                    ("Upper Body Visible", inspection["upper_body_visible"]),
                    ("Lower Body Visible", inspection["lower_body_visible"]),
                ]

                for label, passed in checks:

                    if passed:
                        text = f"[OK] {label}"
                        color = (0, 255, 0)
                    else:
                        text = f"[X] {label}"
                        color = (0, 0, 255)

                    cv2.putText(
                        annotated,
                        text,
                        (10, y_text),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2
                    )

                    y_text += 30

                # ===============================
                # Overall Status
                # ===============================

                y_text += 15

                if (
                    inspection["upper_body_visible"] and
                    inspection["lower_body_visible"]
                ):
                    status = "Status: Ready for Inspection"
                    color = (0, 255, 0)
                else:
                    status = "Status: Please stand properly"
                    color = (0, 0, 255)

                cv2.putText(
                    annotated,
                    status,
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

    cv2.imshow("AI Dress Code - Stage 2.5", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()