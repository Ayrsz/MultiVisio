import cv2
from ultralytics import YOLO

#model = YOLO("yolo11n.pt")   # se télécharge tout seul au premier lancement
#model = YOLO("runs/detect/train-2/weights/best.pt")
model = YOLO("best_1h.pt") 
cap = cv2.VideoCapture(0)    # 0 = webcam du PC

while True:
    ok, frame = cap.read()
    if not ok:
        break
    results = model(frame, conf=0.8, verbose=False)
    cv2.imshow("Detection", results[0].plot())
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
