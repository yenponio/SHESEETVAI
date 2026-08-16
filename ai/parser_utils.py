from collections import Counter

def get_majority_label(mask, parser, x, y, radius=7):

    h, w = mask.shape

    x = int(x)
    y = int(y)

    x1 = max(0, x - radius)
    x2 = min(w, x + radius + 1)

    y1 = max(0, y - radius)
    y2 = min(h, y + radius + 1)

    region = mask[y1:y2, x1:x2]

    labels = region.flatten().tolist()

    majority_id = Counter(labels).most_common(1)[0][0]

    return majority_id, parser.get_label_name(majority_id)


def get_majority_label_in_region(mask, parser, x1, y1, x2, y2):

    h, w = mask.shape

    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(w, int(x2))
    y2 = min(h, int(y2))

    region = mask[y1:y2, x1:x2]

    if region.size == 0:
        return None, "background"

    labels = region.flatten().tolist()

    majority_id = Counter(labels).most_common(1)[0][0]

    return majority_id, parser.get_label_name(majority_id)

def get_label_percentage_in_region(
    mask,
    parser,
    x1,
    y1,
    x2,
    y2,
    valid_labels
):

    h, w = mask.shape

    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(w, int(x2))
    y2 = min(h, int(y2))

    region = mask[y1:y2, x1:x2]

    if region.size == 0:
        return 0

    labels = []

    for value in region.flatten():
        labels.append(
            parser.get_label_name(int(value))
        )

    total_pixels = len(labels)

    covered_pixels = sum(
        1 for label in labels
        if label in valid_labels
    )

    coverage = covered_pixels / total_pixels

    return coverage