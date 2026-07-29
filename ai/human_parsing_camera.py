import cv2
import numpy as np
from fashn_human_parser import FashnHumanParser

print("Loading Human Parser...")
parser = FashnHumanParser()
print("Human Parser Loaded!")

cap = cv2.VideoCapture(0)

# One color for each class (18 classes)
colors = np.array([
    [0, 0, 0],         # background
    [255, 220, 177],   # face
    [0, 255, 255],     # hair
    [0, 255, 0],       # top
    [255, 0, 255],     # dress
    [255, 255, 0],     # skirt
    [255, 0, 0],       # pants
    [128, 0, 128],     # belt
    [0, 128, 255],     # bag
    [0, 0, 255],       # hat
    [255, 128, 0],     # scarf
    [128, 255, 255],   # glasses
    [180, 105, 255],   # arms
    [80, 180, 255],    # hands
    [50, 150, 255],    # legs
    [100, 255, 100],   # feet
    [180, 180, 180],   # torso
    [255, 255, 255],   # jewelry
], dtype=np.uint8)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Human Parsing
    mask = parser.predict(frame)

    # Convert class IDs into colors
    color_mask = colors[mask]

    # Blend mask with original image
    overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)

    cv2.imshow("Original", frame)
    cv2.imshow("Segmentation", overlay)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()