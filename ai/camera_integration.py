import cv2
from ultralytics import YOLO
from fashn_human_parser import FashnHumanParser
from shoulder_detector import detect_shoulders
from pose_utils import build_body_keypoints
from midriff_detector import detect_midriff


print("Loading YOLO Pose...")
pose_model = YOLO("yolov8n-pose.pt")

print("Loading Human Parser...")
parser = FashnHumanParser()

print("All AI Models Loaded!")

CONF = 0.5

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

cap = cv2.VideoCapture(0)

printed_mask_info = False

while True:

    ret, frame = cap.read()

    if not ret:
        break

    mask = parser.predict(frame)

    if not printed_mask_info:
        print("Human Parsing Mask Shape:", mask.shape)
        printed_mask_info = True

    results = pose_model.predict(frame, verbose=False)

    annotated = frame.copy()

    if len(results):

        r = results[0]

        annotated = r.plot()

        if r.keypoints is not None:

            data = r.keypoints.data.cpu().numpy()

            if len(data):

                person = data[0]

                body = build_body_keypoints(
                    person,
                    KEYPOINTS,
                    CONF
                )

                shoulders = detect_shoulders(
                    mask,
                    parser,
                    body
                )
                midriff = detect_midriff(
                     mask,
                     parser,
                    body
                )

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

                y_text += 10

                cv2.putText(
                    annotated,
                    f"Left Shoulder : {shoulders['left_label']}",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

                y_text += 30

                cv2.putText(
                    annotated,
                    f"Right Shoulder: {shoulders['right_label']}",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

                y_text += 30

                if shoulders["covered"]:
                    shoulder_status = "Shoulders: PASS"
                    shoulder_color = (0, 255, 0)
                else:
                    shoulder_status = "Shoulders: FAIL"
                    shoulder_color = (0, 0, 255)

                cv2.putText(
                    annotated,
                    shoulder_status,
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    shoulder_color,
                    2
                )
                y_text += 30

                cv2.putText(
                    annotated,
                    f"Midriff Coverage: {midriff['coverage'] * 100:.1f}%",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

                y_text += 30

                if midriff["covered"]:
                    midriff_status = "Midriff: PASS"
                    midriff_color = (0, 255, 0)
                else:
                    midriff_status = "Midriff: FAIL"
                    midriff_color = (0, 0, 255)

                cv2.putText(
                    annotated,
                    midriff_status,
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    midriff_color,
                    2
                )

                y_text += 30

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

    cv2.imshow("AI Dress Code - Integration Test", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()