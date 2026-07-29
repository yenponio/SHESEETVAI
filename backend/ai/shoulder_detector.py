from parser_utils import get_majority_label

VALID_UPPER_CLOTHING = [
    "top",
    "dress"
]


def detect_shoulders(mask, parser, body):

    _, left_name = get_majority_label(
        mask,
        parser,
        body["Left Shoulder"]["x"],
        body["Left Shoulder"]["y"]
    )

    _, right_name = get_majority_label(
        mask,
        parser,
        body["Right Shoulder"]["x"],
        body["Right Shoulder"]["y"]
    )

    left_covered = left_name in VALID_UPPER_CLOTHING
    right_covered = right_name in VALID_UPPER_CLOTHING

    return {
        "left_label": left_name,
        "right_label": right_name,
        "left_covered": left_covered,
        "right_covered": right_covered,
        "covered": left_covered and right_covered
    }