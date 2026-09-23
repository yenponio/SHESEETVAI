import cv2
import time
import os
from collections import Counter
from datetime import datetime

from ultralytics import YOLO
from fashn_human_parser import FashnHumanParser

from shoulder_detector import detect_shoulders
from pose_utils import build_body_keypoints
from midriff_detector import detect_midriff
from knee_detector import detect_knees
from dress_code_checker import check_dress_code


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POSE_MODEL_PATH = os.path.join(
    BASE_DIR,
    "yolov8n-pose.pt"
)

CAPTURE_FOLDER = os.path.join(
    BASE_DIR,
    "captures"
)

os.makedirs(
    CAPTURE_FOLDER,
    exist_ok=True
)


# ==========================================================
# LOAD AI MODELS
# ==========================================================

print("Loading YOLO Pose...")

pose_model = YOLO(
    POSE_MODEL_PATH
)

print("Loading Human Parser...")

parser = FashnHumanParser()

print("All AI Models Loaded!")


# ==========================================================
# SETTINGS
# ==========================================================

CONF = 0.5

REQUIRED_STABLE_TIME = 1.0

INSPECTION_FRAMES = 5


# ==========================================================
# YOLO KEYPOINTS
# ==========================================================

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


# ==========================================================
# AI INSPECTION ENGINE
# ==========================================================

class DressCodeInspection:

    def __init__(self):

        self.reset()


    # ======================================================
    # RESET FOR NEW STUDENT
    # ======================================================

    def reset(self):

        self.inspection_state = "WAITING"

        self.stable_start_time = None

        self.inspection_count = 0

        self.inspection_results = []

        self.final_result = None

        self.recorded_violations = []

        self.screenshot_saved = False

        self.screenshot_path = None

        self.printed_mask_info = False

        self.finished = False

        print("")
        print("========================================")
        print("AI READY FOR NEW STUDENT")
        print("========================================")


    # ======================================================
    # RETURN CURRENT RESULT
    # ======================================================

    def get_result(self):

        return {
            "finished": self.finished,
            "status": self.final_result,
            "violations": self.recorded_violations,
            "screenshot": self.screenshot_path,
        }


    # ======================================================
    # PROCESS ONE CAMERA FRAME
    # ======================================================

    def process_frame(self, frame):

        if frame is None:

            return frame, self.get_result()


        # If already finished, don't process again
        if self.finished:

            return frame, self.get_result()


        # ==================================================
        # YOLO POSE
        # ==================================================

        results = pose_model.predict(
            frame,
            verbose=False
        )

        annotated = frame.copy()


        if not results:

            return annotated, self.get_result()


        result = results[0]

        annotated = result.plot()
        # Preserve pose/box overlays before any display/debug text is drawn.
        evidence_frame = annotated.copy()


        if result.keypoints is None:

            self.stable_start_time = None

            self.draw_waiting_message(
                annotated,
                "No student detected"
            )

            return annotated, self.get_result()


        data = (
            result.keypoints.data
            .cpu()
            .numpy()
        )


        if len(data) == 0:

            self.stable_start_time = None

            self.draw_waiting_message(
                annotated,
                "No student detected"
            )

            return annotated, self.get_result()


        # ==================================================
        # USE FIRST DETECTED PERSON
        # ==================================================

        person = data[0]

        body = build_body_keypoints(
            person,
            KEYPOINTS,
            CONF
        )


        # ==================================================
        # BODY VISIBILITY
        # ==================================================

        upper_body_visible = (
            body["Left Shoulder"]["visible"]
            and
            body["Right Shoulder"]["visible"]
        )

        hips_visible = (
            body["Left Hip"]["visible"]
            and
            body["Right Hip"]["visible"]
        )

        knees_visible = (
            body["Left Knee"]["visible"]
            and
            body["Right Knee"]["visible"]
        )

        ankles_visible = (
            body["Left Ankle"]["visible"]
            and
            body["Right Ankle"]["visible"]
        )

        full_body_visible = (
            upper_body_visible
            and hips_visible
            and knees_visible
            and ankles_visible
        )


        # ==================================================
        # DISPLAY BODY CHECKS
        # ==================================================

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
            ("Student Detected", True),
            (
                "Shoulders Visible",
                upper_body_visible
            ),
            (
                "Hips Visible",
                hips_visible
            ),
            (
                "Knees Visible",
                knees_visible
            ),
            (
                "Ankles Visible",
                ankles_visible
            ),
        ]


        for label, passed in checks:

            if passed:

                text = f"[OK] {label}"

                color = (
                    0,
                    255,
                    0
                )

            else:

                text = f"[X] {label}"

                color = (
                    0,
                    0,
                    255
                )


            cv2.putText(
                annotated,
                text,
                (10, y_text),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2
            )

            y_text += 27


        # ==================================================
        # WAITING FOR FULL BODY
        # ==================================================

        if self.inspection_state == "WAITING":

            if full_body_visible:

                if self.stable_start_time is None:

                    self.stable_start_time = (
                        time.monotonic()
                    )

                    print("")
                    print(
                        "Full body detected."
                    )

                    print(
                        "Waiting for stable position..."
                    )


                stable_time = (
                    time.monotonic()
                    -
                    self.stable_start_time
                )


                remaining = max(
                    0,
                    REQUIRED_STABLE_TIME
                    -
                    stable_time
                )


                cv2.putText(
                    annotated,
                    "Full body detected",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

                y_text += 30


                cv2.putText(
                    annotated,
                    f"Preparing inspection: "
                    f"{remaining:.1f}s",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )


                # ==========================================
                # FULL BODY STABLE
                # ==========================================

                if (
                    stable_time
                    >= REQUIRED_STABLE_TIME
                ):

                    self.inspection_state = (
                        "INSPECTING"
                    )

                    self.inspection_count = 0

                    self.inspection_results = []


                    print("")
                    print(
                        "========================================"
                    )

                    print(
                        "FULL BODY POSITION CONFIRMED"
                    )

                    print(
                        "Starting Human Parser inspection..."
                    )

                    print(
                        "========================================"
                    )


            else:

                self.stable_start_time = None

                cv2.putText(
                    annotated,
                    "Please show full body",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2
                )

                y_text += 30

                cv2.putText(
                    annotated,
                    "Shoulders to ankles required",
                    (10, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2
                )


        # ==================================================
        # HUMAN PARSER INSPECTION
        # ==================================================

        if self.inspection_state == "INSPECTING":

            cv2.putText(
                annotated,
                "Human Parser: ON",
                (10, y_text),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            y_text += 30


            cv2.putText(
                annotated,
                (
                    f"Inspection: "
                    f"{self.inspection_count + 1}/"
                    f"{INSPECTION_FRAMES}"
                ),
                (10, y_text),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            y_text += 35


            print(
                f"Running Human Parser "
                f"{self.inspection_count + 1}/"
                f"{INSPECTION_FRAMES}..."
            )


            # ==============================================
            # HUMAN PARSING
            # ==============================================

            mask = parser.predict(
                frame
            )


            if not self.printed_mask_info:

                print(
                    "Human Parsing Mask Shape:",
                    mask.shape
                )

                self.printed_mask_info = True


            # ==============================================
            # CLOTHING / BODY CHECKS
            # ==============================================

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


            knees = detect_knees(
                mask,
                parser,
                body
            )


            current_result = {
                "shoulders":
                    shoulders["covered"],

                "midriff":
                    midriff["covered"],

                "knees":
                    knees["covered"],
            }


            self.inspection_results.append(
                current_result
            )


            self.inspection_count += 1


            # ==============================================
            # DISPLAY CURRENT RESULTS
            # ==============================================

            shoulder_status = (
                "PASS"
                if shoulders["covered"]
                else "FAIL"
            )

            shoulder_color = (
                (0, 255, 0)
                if shoulders["covered"]
                else (0, 0, 255)
            )


            cv2.putText(
                annotated,
                f"Shoulders: {shoulder_status}",
                (10, y_text),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                shoulder_color,
                2
            )

            y_text += 30


            midriff_status = (
                "PASS"
                if midriff["covered"]
                else "FAIL"
            )

            midriff_color = (
                (0, 255, 0)
                if midriff["covered"]
                else (0, 0, 255)
            )


            cv2.putText(
                annotated,
                (
                    f"Midriff: "
                    f"{midriff_status} "
                    f"({midriff['coverage'] * 100:.1f}%)"
                ),
                (10, y_text),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                midriff_color,
                2
            )

            y_text += 30


            knee_status = (
                "PASS"
                if knees["covered"]
                else "FAIL"
            )

            knee_color = (
                (0, 255, 0)
                if knees["covered"]
                else (0, 0, 255)
            )


            cv2.putText(
                annotated,
                f"Knees: {knee_status}",
                (10, y_text),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                knee_color,
                2
            )

            y_text += 35


            # ==============================================
            # ALL 5 FRAMES COMPLETE
            # ==============================================

            if (
                self.inspection_count
                >= INSPECTION_FRAMES
            ):

                self.finish_inspection(
                    evidence_frame
                )


        # ==================================================
        # FINAL RESULT
        # ==================================================

        if self.inspection_state == "FINISHED":

            self.draw_final_result(
                annotated
            )


        return (
            annotated,
            self.get_result()
        )


    # ======================================================
    # FINISH INSPECTION
    # ======================================================

    def finish_inspection(
        self,
        evidence_frame
    ):

        print("")
        print(
            "========================================"
        )

        print(
            "ALL INSPECTION FRAMES COMPLETE"
        )

        print(
            "========================================"
        )


        shoulder_votes = [
            result["shoulders"]
            for result
            in self.inspection_results
        ]


        midriff_votes = [
            result["midriff"]
            for result
            in self.inspection_results
        ]


        knee_votes = [
            result["knees"]
            for result
            in self.inspection_results
        ]


        final_shoulders_covered = (
            Counter(
                shoulder_votes
            ).most_common(1)[0][0]
        )


        final_midriff_covered = (
            Counter(
                midriff_votes
            ).most_common(1)[0][0]
        )


        final_knees_covered = (
            Counter(
                knee_votes
            ).most_common(1)[0][0]
        )


        final_shoulders = {
            "covered":
                final_shoulders_covered
        }


        final_midriff = {
            "covered":
                final_midriff_covered
        }


        final_knees = {
            "covered":
                final_knees_covered
        }


        # ==================================================
        # FINAL DRESS CODE CHECK
        # ==================================================

        final_check = check_dress_code(
            final_shoulders,
            final_midriff,
            final_knees
        )


        if final_check["passed"]:

            self.final_result = "PASS"

        else:

            self.final_result = (
                "VIOLATION"
            )


        self.recorded_violations = (
            final_check["violations"]
        )


        self.inspection_state = (
            "FINISHED"
        )


        # ==================================================
        # Display overlays are drawn separately in process_frame.
        # Evidence retains the actual camera image and pose overlays only.


        # ==================================================
        # SAVE SCREENSHOT
        # ==================================================

        timestamp = (
            datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )


        filename = (
            f"inspection_{timestamp}.jpg"
        )


        screenshot_path = (
            os.path.join(
                CAPTURE_FOLDER,
                filename
            )
        )


        success = cv2.imwrite(
            screenshot_path,
            evidence_frame
        )


        if success:

            self.screenshot_saved = True

            self.screenshot_path = (
                screenshot_path
            )

            print(
                "Final inspection screenshot saved:"
            )

            print(
                screenshot_path
            )

        else:

            print(
                "ERROR: Could not save screenshot."
            )


        # ==================================================
        # PRINT RESULT
        # ==================================================

        print("")
        print(
            "========================================"
        )

        print(
            f"Dress Code Result: "
            f"{self.final_result}"
        )


        if self.recorded_violations:

            print("Violations:")

            for violation in (
                self.recorded_violations
            ):

                print(
                    f"- {violation}"
                )

        else:

            print(
                "Violations: None"
            )


        print(
            "========================================"
        )


        # THIS IS THE IMPORTANT SIGNAL
        # camera_server.py will see this
        # and close the camera.

        self.finished = True


    # ======================================================
    # FINAL RESULT OVERLAY
    # ======================================================

    def draw_final_result(
        self,
        frame
    ):

        if self.final_result == "PASS":

            final_text = (
                "DRESS CODE: PASS"
            )

            final_color = (
                0,
                255,
                0
            )

        else:

            final_text = (
                "DRESS CODE: VIOLATION"
            )

            final_color = (
                0,
                0,
                255
            )


        cv2.rectangle(
            frame,
            (5, 5),
            (500, 150),
            (0, 0, 0),
            -1
        )


        cv2.putText(
            frame,
            final_text,
            (15, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            final_color,
            2
        )


        y = 75


        if self.recorded_violations:

            for violation in (
                self.recorded_violations
            ):

                cv2.putText(
                    frame,
                    f"- {violation}",
                    (15, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 0, 255),
                    2
                )

                y += 25

        else:

            cv2.putText(
                frame,
                "Violations: None",
                (15, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )


    # ======================================================
    # WAITING MESSAGE
    # ======================================================

    def draw_waiting_message(
        self,
        frame,
        message
    ):

        cv2.putText(
            frame,
            "AI Dress Code Inspection",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            message,
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )