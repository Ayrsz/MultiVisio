import cv2
from collections import defaultdict, deque
from ultralytics import YOLO

#Un premier script permetttant de rajouter le tracking

model = YOLO("best2.pt")
cap = cv2.VideoCapture(0)  # ou 0 pour la webcam

trails = defaultdict(lambda: deque(maxlen=60))  # 60 derniers points par drone

while True:
    ok, frame = cap.read()
    if not ok:
        break

    results = model.track(frame, persist=True, tracker="botsort.yaml",
                          conf=0.7, verbose=False)
    r = results[0]
    annotated = r.plot()   # affiche déjà boîtes + ID

    if r.boxes.id is not None:
        centres = r.boxes.xywh.cpu().tolist()
        ids = r.boxes.id.int().cpu().tolist()
        for (x, y, w, h), tid in zip(centres, ids):
            trails[tid].append((int(x), int(y)))
            pts = list(trails[tid])
            for i in range(1, len(pts)):
                cv2.line(annotated, pts[i - 1], pts[i], (0, 255, 255), 2)

    cv2.imshow("Tracking", annotated)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()