from parser_utils import get_label_percentage_in_region



VALID_COVERAGE = {
    "top",
    "dress"
}


MIN_COVERAGE = 0.90


def detect_midriff(mask, parser, body):

    left_shoulder = body["Left Shoulder"]
    right_shoulder = body["Right Shoulder"]
    left_hip = body["Left Hip"]
    right_hip = body["Right Hip"]

    shoulder_y = (
        left_shoulder["y"] +
        right_shoulder["y"]
    ) / 2

    hip_y = (
        left_hip["y"] +
        right_hip["y"]
    ) / 2


    mid_y1 = shoulder_y + (hip_y - shoulder_y) * 0.65
    mid_y2 = shoulder_y + (hip_y - shoulder_y) * 0.95


    hip_center = (
        left_hip["x"] +
        right_hip["x"]
    ) / 2

    hip_width = abs(
        right_hip["x"] -
        left_hip["x"]
    )

    x1 = hip_center - (hip_width * 0.35)
    x2 = hip_center + (hip_width * 0.35)


    coverage = get_label_percentage_in_region(
        mask,
        parser,
        x1,
        mid_y1,
        x2,
        mid_y2,
        VALID_COVERAGE
    )


    return {
        "coverage": coverage,
        "covered": coverage >= MIN_COVERAGE
    }