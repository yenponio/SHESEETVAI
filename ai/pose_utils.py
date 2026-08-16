def build_body_keypoints(person, keypoints, conf_threshold):
    """
    Converts YOLO Pose keypoints into an easy-to-use dictionary.
    """

    body = {}

    for idx, kp in enumerate(person):

        x, y, conf = kp

        body[keypoints[idx]] = {
            "x": float(x),
            "y": float(y),
            "conf": float(conf),
            "visible": conf > conf_threshold
        }

    return body