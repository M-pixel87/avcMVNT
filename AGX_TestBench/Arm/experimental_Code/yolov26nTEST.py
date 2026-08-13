import cv2
from ultralytics import YOLO

model = YOLO("/home/uafs/Downloads/weights(2).pt")

cap = cv2.VideoCapture(1)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    results = model(frame)

    annotated_frame = results[0].plot()

    cv2.imshow("Yolov26n Model Test", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()