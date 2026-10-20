"""detect_camera.py + envoi d'une alerte au téléphone quand un drone est vu.

Lancer :  python detect_et_alerte.py
Quitter : touche "q" dans la fenêtre vidéo.
"""

import cv2
from ultralytics import YOLO

from alerte_drone import envoyer_alerte

model = YOLO("best_1h.pt")   # le modèle entraîné sur les drones
cap = cv2.VideoCapture(0)    # 0 = webcam du PC (plus tard : le flux de l'ESP32-CAM)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    results = model(frame, conf=0.8, verbose=False)

    # S'il y a au moins une détection, on prévient le téléphone
    boites = results[0].boxes
    if len(boites) > 0:
        envoyer_alerte(confiance=float(boites.conf.max()))

    cv2.imshow("Detection", results[0].plot())
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
