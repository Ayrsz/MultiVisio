import cv2
from pathlib import Path
from ultralytics import YOLO

# Applique le modèle entrainé à chaque image de la vidéo (sans en sauter),
# Ne fait pas du direct, c'est à partir d'une vidéo déjà enregistrée
# et enregistre une vidéo annotée avec les boîtes de détection.

# ---------- RÉGLAGES ----------
VIDEO_ENTREE = r"esp32.mp4"      # la vidéo à analyser
MODELE = "best2.pt"
CONF = 0.6
SUIVI = False                       # True = ajoute les ID de suivi (ByteTrack)
APERCU = True                       # True = affiche la vidéo pendant le traitement ('q' pour arrêter)
# ------------------------------

entree = Path(VIDEO_ENTREE)
sortie = entree.with_name(f"{entree.stem}_annote_VDE_{MODELE}.mp4")

model = YOLO(MODELE)
cap = cv2.VideoCapture(str(entree))
if not cap.isOpened():
    raise SystemExit(f"Impossible d'ouvrir la vidéo : {entree}")

fps = cap.get(cv2.CAP_PROP_FPS) or 30
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"{entree.name} : {w}x{h}, {fps:.1f} images/s, {total} images")

writer = cv2.VideoWriter(str(sortie), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

n = n_detections = 0
try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if SUIVI:
            r = model.track(frame, persist=True, conf=CONF, verbose=False)[0]
        else:
            r = model(frame, conf=CONF, verbose=False)[0]

        n_detections += len(r.boxes)
        annotee = r.plot()
        writer.write(annotee)
        n += 1

        if n % 50 == 0:
            print(f"  {n}/{total} images traitées")
        if APERCU:
            cv2.imshow("Traitement (q pour arrêter)", annotee)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Arrêt demandé.")
                break
finally:
    cap.release()
    writer.release()
    cv2.destroyAllWindows()

print(f"\nTerminé : {n} images, {n_detections} détections au total")
print(f"Vidéo annotée : {sortie.resolve()}")
