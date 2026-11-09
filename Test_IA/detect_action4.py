"""Détection de drones avec la DJI Osmo Action 4 branchée en mode Webcam,
avec un panneau qui affiche en direct les paramètres d'acquisition vidéo.

Lancer (dans Test_IA, à côté de best_1h.pt) :
    python detect_action4.py              # cherche la caméra tout seul
    python detect_action4.py --cam 1      # force la caméra n°1
    python detect_action4.py --track      # suivi (un ID par drone) au lieu de la simple détection

Touches dans la fenêtre :
    q = quitter   h = cacher/afficher le panneau   s = capture d'écran
"""

import argparse
import platform
import time
from collections import deque
from datetime import datetime

import cv2
from ultralytics import YOLO

# Sous Windows, DirectShow permet de choisir la résolution de façon fiable
BACKEND = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY

# Propriétés que la caméra peut (ou non) renvoyer à OpenCV
PROPRIETES = {
    "Exposition": cv2.CAP_PROP_EXPOSURE,
    "Expo auto": cv2.CAP_PROP_AUTO_EXPOSURE,
    "Gain": cv2.CAP_PROP_GAIN,
    "Luminosite": cv2.CAP_PROP_BRIGHTNESS,
    "Contraste": cv2.CAP_PROP_CONTRAST,
    "Saturation": cv2.CAP_PROP_SATURATION,
    "Nettete": cv2.CAP_PROP_SHARPNESS,
    "Gamma": cv2.CAP_PROP_GAMMA,
    "Balance blancs": cv2.CAP_PROP_WB_TEMPERATURE,
    "BdB auto": cv2.CAP_PROP_AUTO_WB,
    "Mise au point": cv2.CAP_PROP_FOCUS,
    "Zoom": cv2.CAP_PROP_ZOOM,
}


def fourcc_texte(valeur):
    """Transforme le code FOURCC (un nombre) en texte lisible, ex. 'MJPG'."""
    v = int(valeur)
    texte = "".join(chr((v >> 8 * i) & 0xFF) for i in range(4))
    return texte if texte.strip("\x00").isprintable() and v else "n/d"


def ouvrir_camera(index, largeur, hauteur, fps):
    cap = cv2.VideoCapture(index, BACKEND)
    if not cap.isOpened():
        return None
    # MJPG d'abord : sinon beaucoup de caméras USB restent bloquées en basse résolution
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, largeur)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hauteur)
    cap.set(cv2.CAP_PROP_FPS, fps)
    ok, _ = cap.read()
    if not ok:
        cap.release()
        return None
    return cap


def chercher_camera(largeur, hauteur, fps):
    """Essaie les caméras 0 à 4 et garde celle qui a la plus grande résolution.
    La webcam intégrée d'un portable est souvent la n°0, l'Action 4 la n°1."""
    trouvees = []
    for i in range(5):
        cap = ouvrir_camera(i, largeur, hauteur, fps)
        if cap is None:
            continue
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"  caméra {i} : {w}x{h}")
        trouvees.append((w * h, i))
        cap.release()
    if not trouvees:
        return None
    return max(trouvees)[1]


def lire_proprietes(cap):
    """Lit les réglages renvoyés par la caméra. -1 ou 0 veut souvent dire 'non fourni'."""
    infos = {}
    for nom, prop in PROPRIETES.items():
        v = cap.get(prop)
        infos[nom] = "n/d" if v in (-1, 0) else f"{v:g}"
    return infos


def dessiner_panneau(img, lignes):
    """Panneau semi-transparent en haut à gauche, avec une ligne par paramètre."""
    taille, epaisseur, interligne = 0.5, 1, 20
    largeur = max(cv2.getTextSize(l, cv2.FONT_HERSHEY_SIMPLEX, taille, epaisseur)[0][0]
                  for l in lignes) + 20
    hauteur = interligne * len(lignes) + 12
    fond = img.copy()
    cv2.rectangle(fond, (0, 0), (largeur, hauteur), (0, 0, 0), -1)
    cv2.addWeighted(fond, 0.6, img, 0.4, 0, img)
    for i, l in enumerate(lignes):
        couleur = (0, 255, 255) if l.startswith("--") else (255, 255, 255)
        cv2.putText(img, l, (10, 20 + i * interligne), cv2.FONT_HERSHEY_SIMPLEX,
                    taille, couleur, epaisseur, cv2.LINE_AA)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cam", type=int, default=None, help="numéro de la caméra (sinon recherche auto)")
    p.add_argument("--modele", default="best_1h.pt")
    p.add_argument("--conf", type=float, default=0.5, help="seuil de confiance YOLO")
    p.add_argument("--imgsz", type=int, default=640, help="taille d'image donnée à YOLO")
    p.add_argument("--largeur", type=int, default=1920)
    p.add_argument("--hauteur", type=int, default=1080)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--track", action="store_true", help="suivi ByteTrack (un ID par drone)")
    args = p.parse_args()

    index = args.cam
    if index is None:
        print("Recherche des caméras…")
        index = chercher_camera(args.largeur, args.hauteur, args.fps)
        if index is None:
            print("Aucune caméra trouvée. L'Action 4 est-elle bien en mode Webcam ?")
            return
    cap = ouvrir_camera(index, args.largeur, args.hauteur, args.fps)
    if cap is None:
        print(f"Impossible d'ouvrir la caméra {index}.")
        return

    model = YOLO(args.modele)
    nom_backend = cap.getBackendName()
    fps_annonce = cap.get(cv2.CAP_PROP_FPS)
    fourcc = fourcc_texte(cap.get(cv2.CAP_PROP_FOURCC))

    # Récapitulatif dans le terminal
    print(f"\nCaméra {index} ouverte via {nom_backend}")
    print(f"  résolution demandée : {args.largeur}x{args.hauteur} @ {args.fps} fps")
    print(f"  résolution obtenue  : {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x"
          f"{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} @ {fps_annonce:g} fps, codec {fourcc}")
    for nom, v in lire_proprietes(cap).items():
        print(f"  {nom:<15}: {v}")
    print("\nq = quitter, h = panneau, s = capture\n")

    temps_images = deque(maxlen=30)   # pour calculer le FPS réel sur ~1 s
    temps_infer = deque(maxlen=30)
    n_image, voir_panneau = 0, True
    infos = lire_proprietes(cap)

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Plus d'image : caméra débranchée ou sortie du mode Webcam ?")
            break
        n_image += 1
        temps_images.append(time.perf_counter())

        t0 = time.perf_counter()
        if args.track:
            res = model.track(frame, conf=args.conf, imgsz=args.imgsz, persist=True,
                              tracker="bytetrack.yaml", verbose=False)[0]
        else:
            res = model(frame, conf=args.conf, imgsz=args.imgsz, verbose=False)[0]
        temps_infer.append((time.perf_counter() - t0) * 1000)

        image = res.plot()

        # Les réglages de la caméra changent peu : on les relit une fois par seconde
        if n_image % 30 == 0:
            infos = lire_proprietes(cap)

        if voir_panneau:
            fps_reel = ((len(temps_images) - 1) / (temps_images[-1] - temps_images[0])
                        if len(temps_images) > 1 else 0)
            h, w = frame.shape[:2]
            boites = res.boxes
            conf_max = f"{float(boites.conf.max()):.2f}" if len(boites) else "-"
            ids = (", ".join(str(int(i)) for i in boites.id)
                   if args.track and boites.id is not None else "-")
            lignes = [
                "-- ACQUISITION",
                f"Camera #{index}  ({nom_backend})",
                f"Resolution : {w}x{h}",
                f"Codec : {fourcc}",
                f"FPS annonce : {fps_annonce:g}",
                f"FPS reel : {fps_reel:.1f}",
                f"Image #{n_image}",
                f"Heure : {datetime.now():%H:%M:%S}",
                "-- REGLAGES CAMERA",
                *[f"{nom} : {v}" for nom, v in infos.items()],
                "-- IA",
                f"Modele : {args.modele}",
                f"Mode : {'suivi ByteTrack' if args.track else 'detection'}",
                f"imgsz : {args.imgsz}   conf : {args.conf}",
                f"Inference : {sum(temps_infer) / len(temps_infer):.0f} ms",
                f"Drones : {len(boites)}   conf max : {conf_max}",
            ]
            if args.track:
                lignes.append(f"IDs : {ids}")
            dessiner_panneau(image, lignes)

        cv2.imshow("MultiVisio - Action 4", image)
        touche = cv2.waitKey(1) & 0xFF
        if touche == ord("q"):
            break
        if touche == ord("h"):
            voir_panneau = not voir_panneau
        if touche == ord("s"):
            nom = f"capture_{datetime.now():%Y%m%d_%H%M%S}.jpg"
            cv2.imwrite(nom, image)
            print(f"Capture enregistrée : {nom}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
