import cv2
import time
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO

#Ouvre la webcam(avec 0) ou le flux ESP32 (avec l'URL)
#Fait tourner le modèle YOLO en direct
#Et enregistre les vidéos brutes et annotées dans le dossier "enregistrements"

MODEL = "best_1h.pt"
model = YOLO(MODEL)
url = "http://10.170.243.130:81/stream"
cap = cv2.VideoCapture(0)   # 0 = webcam du PC ; remplacer par url pour l'ESP32

FPS_ENREG = 15              # fps des vidéos enregistrées (à ajuster, voir plus bas)
ENREGISTRER_BRUT = True     # vidéo sans les boîtes
ENREGISTRER_ANNOTE = True   # vidéo avec les boîtes

dossier = Path("enregistrements")
dossier.mkdir(exist_ok=True)
horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")

writer_brut = None
writer_annote = None
n_images = 0
t0 = time.time()

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        results = model(frame, conf=0.7, verbose=False)
        annotee = results[0].plot()

        # création des fichiers vidéo au premier passage (on connaît alors la taille de l'image)
        if writer_brut is None:
            h, w = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            if ENREGISTRER_BRUT:
                writer_brut = cv2.VideoWriter(str(dossier / f"{horodatage}_brut.mp4"),
                                              fourcc, FPS_ENREG, (w, h))
            if ENREGISTRER_ANNOTE:
                writer_annote = cv2.VideoWriter(str(dossier / f"{horodatage}_annote_{MODEL}.mp4"),
                                                fourcc, FPS_ENREG, (w, h))

        if writer_brut is not None:
            writer_brut.write(frame)
        if writer_annote is not None:
            writer_annote.write(annotee)
        n_images += 1

        cv2.imshow("Detection", annotee)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cap.release()
    if writer_brut is not None:
        writer_brut.release()
    if writer_annote is not None:
        writer_annote.release()
    cv2.destroyAllWindows()
    duree = time.time() - t0
    if duree > 0 and n_images > 0:
        print(f"{n_images} images en {duree:.1f} s -> FPS réel moyen : {n_images / duree:.1f}")
    print(f"Vidéos enregistrées dans : {dossier.resolve()}")