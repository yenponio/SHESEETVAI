from flask import (
    Flask,
    Response,
    jsonify,
    request,
)

from flask_cors import CORS

import cv2
import threading
import time
import os
import json
import requests

from camera_integration import DressCodeInspection


# =====================================================
# FLASK
# =====================================================

app = Flask(__name__)
CORS(app)


# =====================================================
# DJANGO
# =====================================================

DJANGO_AI_RESULT_URL = (
    "http://127.0.0.1:8000/"
    "api/students/ai-result/"
)


# =====================================================
# CAMERA VARIABLES
# =====================================================

camera = None
camera_active = False

camera_lock = threading.Lock()


# =====================================================
# CURRENT STUDENT SESSION
# =====================================================
#
# These values are received from StudentPage.jsx
# when a valid barcode is scanned.
#
# =====================================================

current_student_number = None
current_attempt_id = None


# =====================================================
# AI INSPECTION
# =====================================================

inspection = DressCodeInspection()


latest_result = {

    "finished": False,

    "status": None,

    "violations": [],

    "screenshot": None,

    "sent_to_django": False,

    "django_inspection_id": None,

}


# =====================================================
# SEND AI RESULT TO DJANGO
# =====================================================

def send_result_to_django(result):

    global current_student_number
    global current_attempt_id
    global latest_result

    print("")
    print(
        "========================================"
    )

    print(
        "PREPARING AI RESULT FOR DJANGO"
    )

    print(
        "========================================"
    )


    # =================================================
    # CHECK STUDENT
    # =================================================

    if not current_student_number:

        print(
            "ERROR: No student number "
            "is attached to this AI session."
        )

        latest_result[
            "sent_to_django"
        ] = False

        return False


    result_status = (
        result.get("status")
    )

    violations = (
        result.get(
            "violations",
            []
        )
    )

    screenshot_path = (
        result.get("screenshot")
    )


    print(
        "Student:",
        current_student_number
    )

    print(
        "Attempt ID:",
        current_attempt_id
    )

    print(
        "AI Status:",
        result_status
    )

    print(
        "Violations:",
        violations
    )

    print(
        "Screenshot:",
        screenshot_path
    )


    # =================================================
    # DATA SENT TO DJANGO
    # =================================================

    data = {

        "student_number":
            str(
                current_student_number
            ),

        "status":
            str(
                result_status
            ),

        "violations":
            json.dumps(
                violations
            ),

    }


    if current_attempt_id is not None:

        data["attempt_id"] = str(
            current_attempt_id
        )


    # =================================================
    # VIOLATION
    # =================================================
    #
    # For a violation, screenshot is REQUIRED for the
    # OSA confirmation page.
    #
    # =================================================

    if result_status == "VIOLATION":

        if not screenshot_path:

            print(
                "ERROR: AI reported VIOLATION "
                "but no screenshot path was returned."
            )

            latest_result[
                "sent_to_django"
            ] = False

            return False


        if not os.path.exists(
            screenshot_path
        ):

            print(
                "ERROR: Screenshot file "
                "does not exist:"
            )

            print(
                screenshot_path
            )

            latest_result[
                "sent_to_django"
            ] = False

            return False


        try:

            print("")
            print(
                "Uploading violation screenshot "
                "to Django..."
            )


            with open(
                screenshot_path,
                "rb"
            ) as screenshot_file:

                files = {

                    "screenshot": (

                        os.path.basename(
                            screenshot_path
                        ),

                        screenshot_file,

                        "image/jpeg",

                    )

                }


                response = requests.post(

                    DJANGO_AI_RESULT_URL,

                    data=data,

                    files=files,

                    timeout=30,

                )


        except requests.RequestException as error:

            print("")
            print(
                "ERROR SENDING RESULT TO DJANGO:"
            )

            print(error)

            latest_result[
                "sent_to_django"
            ] = False

            return False


        except OSError as error:

            print("")
            print(
                "ERROR OPENING SCREENSHOT:"
            )

            print(error)

            latest_result[
                "sent_to_django"
            ] = False

            return False


    # =================================================
    # PASS
    # =================================================
    #
    # PASS does not require a screenshot for OSA.
    #
    # =================================================

    else:

        try:

            print("")
            print(
                "Sending PASS result to Django..."
            )


            response = requests.post(

                DJANGO_AI_RESULT_URL,

                data=data,

                timeout=30,

            )


        except requests.RequestException as error:

            print("")
            print(
                "ERROR SENDING RESULT TO DJANGO:"
            )

            print(error)

            latest_result[
                "sent_to_django"
            ] = False

            return False


    # =================================================
    # DJANGO RESPONSE
    # =================================================

    print("")
    print(
        "Django HTTP status:",
        response.status_code
    )


    try:

        django_data = (
            response.json()
        )

    except ValueError:

        django_data = {
            "raw":
                response.text
        }


    print(
        "Django response:",
        django_data
    )


    if not response.ok:

        print(
            "ERROR: Django rejected "
            "the AI result."
        )

        latest_result[
            "sent_to_django"
        ] = False

        return False


    # =================================================
    # SUCCESS
    # =================================================

    latest_result[
        "sent_to_django"
    ] = True


    if isinstance(
        django_data,
        dict
    ):

        latest_result[
            "django_inspection_id"
        ] = django_data.get(
            "inspection_id"
        )


    print("")
    print(
        "========================================"
    )

    print(
        "AI RESULT SUCCESSFULLY SENT TO DJANGO"
    )

    print(
        "========================================"
    )


    return True


# =====================================================
# OPEN CAMERA
# =====================================================

def open_camera():

    global camera
    global camera_active


    with camera_lock:


        if (
            camera is not None
            and camera.isOpened()
        ):

            camera_active = True

            return True


        print("")
        print(
            "========================================"
        )

        print(
            "OPENING CAMERA"
        )

        print(
            "========================================"
        )


        camera = cv2.VideoCapture(
            0,
            cv2.CAP_DSHOW
        )


        if not camera.isOpened():

            print(
                "ERROR: Could not open webcam."
            )

            camera = None

            camera_active = False

            return False


        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640
        )

        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480
        )


        camera_active = True


        print(
            "Camera opened successfully."
        )


        return True


# =====================================================
# RELEASE CAMERA
# =====================================================

def release_camera():

    global camera
    global camera_active


    with camera_lock:

        camera_active = False


        if camera is not None:

            print(
                "Releasing camera..."
            )

            camera.release()

            camera = None


        print(
            "Camera stopped."
        )


# =====================================================
# GENERATE CAMERA + AI FRAMES
# =====================================================

def generate_frames():

    global camera
    global camera_active
    global latest_result


    print("")
    print(
        "========================================"
    )

    print(
        "AI VIDEO STREAM STARTED"
    )

    print(
        "========================================"
    )


    while camera_active:


        # =================================================
        # CHECK CAMERA
        # =================================================

        if camera is None:

            print(
                "Camera object is missing."
            )

            break


        # =================================================
        # READ CAMERA FRAME
        # =================================================

        success, frame = (
            camera.read()
        )


        if not success:

            print(
                "ERROR: Failed to read webcam frame."
            )

            break


        # =================================================
        # REAL DRESS CODE AI
        # =================================================

        try:

            annotated_frame, result = (
                inspection.process_frame(
                    frame
                )
            )


            # ---------------------------------------------
            # IMPORTANT:
            #
            # Preserve server-specific fields while
            # updating the AI result.
            # ---------------------------------------------

            previous_sent = (
                latest_result.get(
                    "sent_to_django",
                    False
                )
            )

            previous_inspection_id = (
                latest_result.get(
                    "django_inspection_id"
                )
            )


            latest_result = dict(
                result
            )


            latest_result[
                "sent_to_django"
            ] = previous_sent


            latest_result[
                "django_inspection_id"
            ] = previous_inspection_id


        except Exception as error:

            print("")
            print(
                "========================================"
            )

            print(
                "AI PROCESSING ERROR"
            )

            print(
                "========================================"
            )

            print(error)

            print(
                "========================================"
            )


            annotated_frame = (
                frame.copy()
            )


            cv2.putText(

                annotated_frame,

                "AI PROCESSING ERROR",

                (20, 50),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 0, 255),

                2

            )


        # =================================================
        # CONVERT FRAME TO JPEG
        # =================================================

        success, buffer = (
            cv2.imencode(
                ".jpg",
                annotated_frame
            )
        )


        if not success:

            continue


        frame_bytes = (
            buffer.tobytes()
        )


        # =================================================
        # SEND FRAME TO REACT
        # =================================================

        yield (

            b"--frame\r\n"

            b"Content-Type: image/jpeg\r\n\r\n"

            + frame_bytes

            + b"\r\n"

        )


        # =================================================
        # AI FINISHED
        # =================================================

        if latest_result.get(
            "finished",
            False
        ):

            print("")
            print(
                "========================================"
            )

            print(
                "AI INSPECTION COMPLETE"
            )

            print(
                "========================================"
            )


            print(
                "Result:",
                latest_result.get(
                    "status"
                )
            )


            violations = (
                latest_result.get(
                    "violations",
                    []
                )
            )


            if violations:

                print(
                    "Violations:"
                )

                for violation in violations:

                    print(
                        f"- {violation}"
                    )

            else:

                print(
                    "Violations: None"
                )


            screenshot = (
                latest_result.get(
                    "screenshot"
                )
            )


            if screenshot:

                print(
                    "Screenshot:"
                )

                print(
                    screenshot
                )


            print(
                "========================================"
            )


            # =================================================
            # SEND RESULT + SCREENSHOT TO DJANGO
            # =================================================

            send_result_to_django(
                latest_result
            )


            # Small delay so browser receives final
            # annotated frame.

            time.sleep(0.3)


            # =================================================
            # STOP CAMERA AFTER AI FINISHES
            # =================================================

            release_camera()


            print(
                "Camera closed because "
                "AI processing is complete."
            )


            break


    print("")
    print(
        "AI video stream ended."
    )


# =====================================================
# START CAMERA + NEW AI SESSION
# =====================================================

@app.route(
    "/start-camera",
    methods=["POST"]
)
def start_camera():

    global latest_result
    global current_student_number
    global current_attempt_id


    print("")
    print(
        "START CAMERA REQUEST RECEIVED"
    )


    # =================================================
    # GET STUDENT INFORMATION FROM REACT
    # =================================================

    request_data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    current_student_number = (
        request_data.get(
            "student_number"
        )
    )


    current_attempt_id = (
        request_data.get(
            "attempt_id"
        )
    )


    print(
        "Student number received:",
        current_student_number
    )

    print(
        "Attempt ID received:",
        current_attempt_id
    )


    # =================================================
    # REQUIRE STUDENT NUMBER
    # =================================================

    if not current_student_number:

        print(
            "ERROR: start-camera request "
            "did not include student_number."
        )

        return jsonify({

            "success": False,

            "message":
                "student_number is required"

        }), 400


    # =================================================
    # RESET AI FOR NEW STUDENT
    # =================================================

    inspection.reset()


    latest_result = {

        "finished": False,

        "status": None,

        "violations": [],

        "screenshot": None,

        "sent_to_django": False,

        "django_inspection_id": None,

    }


    print(
        "AI inspection reset "
        "for new student."
    )


    # =================================================
    # OPEN CAMERA
    # =================================================

    success = open_camera()


    if not success:

        return jsonify({

            "success": False,

            "message":
                "Could not open webcam"

        }), 500


    return jsonify({

        "success": True,

        "message":
            "Camera and AI started",

        "student_number":
            current_student_number,

        "attempt_id":
            current_attempt_id,

    })


# =====================================================
# VIDEO FEED
# =====================================================

@app.route(
    "/video_feed"
)
def video_feed():

    global camera_active


    print(
        "VIDEO FEED REQUEST RECEIVED"
    )


    if not camera_active:

        print(
            "Camera inactive. "
            "Attempting to open camera..."
        )


        success = (
            open_camera()
        )


        if not success:

            return (
                "Could not open camera",
                500
            )


    return Response(

        generate_frames(),

        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )

    )


# =====================================================
# MANUAL STOP CAMERA
# =====================================================

@app.route(
    "/stop-camera",
    methods=["POST"]
)
def stop_camera():

    print(
        "STOP CAMERA REQUEST RECEIVED"
    )


    release_camera()


    return jsonify({

        "success": True,

        "message":
            "Camera stopped"

    })


# =====================================================
# CAMERA STATUS
# =====================================================

@app.route(
    "/camera-status"
)
def camera_status():

    return jsonify({

        "active":
            camera_active,

        "student_number":
            current_student_number,

        "attempt_id":
            current_attempt_id,

        "inspection_finished":
            latest_result.get(
                "finished",
                False
            ),

        "status":
            latest_result.get(
                "status"
            ),

        "violations":
            latest_result.get(
                "violations",
                []
            ),

        "screenshot":
            latest_result.get(
                "screenshot"
            ),

        "sent_to_django":
            latest_result.get(
                "sent_to_django",
                False
            ),

        "django_inspection_id":
            latest_result.get(
                "django_inspection_id"
            ),

    })


# =====================================================
# INSPECTION RESULT
# =====================================================

@app.route(
    "/inspection-result"
)
def inspection_result():

    result = dict(
        latest_result
    )


    result[
        "student_number"
    ] = current_student_number


    result[
        "attempt_id"
    ] = current_attempt_id


    return jsonify(
        result
    )


# =====================================================
# HOME TEST
# =====================================================

@app.route("/")
def home():

    return jsonify({

        "server":
            "SheSeeTV AI Camera Server",

        "camera_active":
            camera_active,

        "student_number":
            current_student_number,

        "inspection_finished":
            latest_result.get(
                "finished",
                False
            ),

    })



# =====================================================
# RESET STUDENT SESSION AFTER OSA REVIEW
# =====================================================

@app.route(
    "/reset-session",
    methods=["POST"]
)
def reset_session():

    global latest_result
    global current_student_number
    global current_attempt_id

    print("")
    print("========================================")
    print("RESETTING SESSION AFTER OSA REVIEW")
    print("========================================")

    # Close the camera if it is still open.
    release_camera()

    # Reset AI state.
    inspection.reset()

    # Clear the previous student session.
    current_student_number = None
    current_attempt_id = None

    latest_result = {
        "finished": False,
        "status": None,
        "violations": [],
        "screenshot": None,
        "sent_to_django": False,
        "django_inspection_id": None,
    }

    print("Previous student session cleared.")
    print("System is ready for the next student.")
    print("========================================")

    return jsonify({
        "success": True,
        "message": "Session reset. Ready for next student."
    })


# =====================================================
# SERVER
# =====================================================

if __name__ == "__main__":

    print("")
    print(
        "========================================"
    )

    print(
        "SHESEETV AI CAMERA SERVER"
    )

    print(
        "========================================"
    )

    print(
        "Waiting for student ID scan..."
    )

    print(
        "Camera is currently OFF."
    )

    print(
        "========================================"
    )


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=False,

        threaded=True,

        use_reloader=False

    )