import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not found")
else:
    print("Camera detected!")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Camera Test", frame)

    if cv2.waitKey(1) == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()