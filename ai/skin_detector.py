import numpy as np


# Human parser body parts considered exposed areas
SKIN_CLASSES = [
    1,   # face
    12,  # arms
    13,  # hands
    14,  # legs
    15   # feet
]


def calculate_skin_percentage(mask, zone):

    x1 = max(zone["top_left"][0], 0)
    y1 = max(zone["top_left"][1], 0)

    x2 = min(zone["bottom_right"][0], mask.shape[1])
    y2 = min(zone["bottom_right"][1], mask.shape[0])


    area = mask[y1:y2, x1:x2]


    if area.size == 0:
        return 0


    skin_pixels = np.isin(
        area,
        SKIN_CLASSES
    )


    percentage = (
        np.sum(skin_pixels)
        /
        area.size
    ) * 100


    return percentage
