import cv2
from ultralytics import YOLO

#Ouvre la webcam(avec 0) ou le flux ESP32 (avec l'URL)
#Fait tourner le modèle YOLO en direct

#model = YOLO("yolo11n.pt")   # se télécharge tout seul au premier lancement
model = YOLO("best2.pt") 
url = "http://10.170.243.130:81/stream"
cap = cv2.VideoCapture(0) # 0 = webcam du PC

while True:
    ok, frame = cap.read()
    if not ok:
        break
    results = model(frame, conf=0.6, verbose=False)
    cv2.imshow("Detection", results[0].plot())
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

