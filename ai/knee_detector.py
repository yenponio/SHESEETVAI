from parser_utils import get_label_percentage_in_region


COVERED_LABELS = {
    "pants",
    "skirt",
    "dress"
}


MIN_COVERAGE = 0.45


def detect_knees(mask, parser, body):

    left_knee = body["Left Knee"]
    right_knee = body["Right Knee"]

    width = 30
    height_top = 35
    height_bottom = 55


    left_coverage = get_label_percentage_in_region(
        mask,
        parser,
        left_knee["x"] - width,
        left_knee["y"] - height_top,
        left_knee["x"] + width,
        left_knee["y"] + height_bottom,
        COVERED_LABELS
    )


    right_coverage = get_label_percentage_in_region(
        mask,
        parser,
        right_knee["x"] - width,
        right_knee["y"] - height_top,
        right_knee["x"] + width,
        right_knee["y"] + height_bottom,
        COVERED_LABELS
    )


    return {
        "left_coverage": left_coverage,
        "right_coverage": right_coverage,

        "covered": (
            left_coverage >= MIN_COVERAGE and
            right_coverage >= MIN_COVERAGE
        )
    }