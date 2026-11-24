"""Détection de drones avec PLUSIEURS caméras en même temps, écran partagé.

Chaque caméra est lue en parallèle et a son propre panneau de paramètres.

Lancer (dans Test_IA, à côté de best_1h.pt) :
    python detect_multi.py                    # prend les 2 premières caméras trouvées
    python detect_multi.py --cams 0 1         # choisit les caméras 0 et 1
    python detect_multi.py --cams 0 1 2       # 3 caméras (ça marche avec autant qu'on veut)
    python detect_multi.py --track            # suivi : un ID par drone, séparé pour chaque caméra
    python detect_multi.py --vertical         # caméras l'une au-dessus de l'autre
    python detect_multi.py --cams 1 192.168.1.42   # caméra USB n°1 + ESP32-CAM en Wi-Fi
                                              # (adresse IP affichée par l'ESP32 au démarrage)

Touches dans la fenêtre :
    q = quitter   h = cacher/afficher les panneaux   s = capture d'écran
"""

import argparse
import platform
import threading
import time
from collections import deque
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO

# Sous Windows, DirectShow permet de choisir la résolution de façon fiable
BACKEND = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY


# ---------------------------------------------------------------- caméra

def fourcc_texte(valeur):
    """Transforme le code FOURCC (un nombre) en texte lisible, ex. 'MJPG'."""
    v = int(valeur)
    texte = "".join(chr((v >> 8 * i) & 0xFF) for i in range(4))
    return texte if texte.strip("\x00").isprintable() and v else "n/d"


def lire_source(texte):
    """'1' -> caméra USB n°1 ; '192.168.1.42' -> flux de l'ESP32-CAM ;
    une adresse complète (http://..., rtsp://...) est gardée telle quelle."""
    if texte.isdigit():
        return int(texte)
    if "://" not in texte:
        # CameraWebServer (exemple Arduino de l'ESP32) diffuse sur le port 81, chemin /stream
        return f"http://{texte}:81/stream"
    return texte


def nom_source(source):
    if isinstance(source, int):
        return f"USB #{source}"
    hote = source.split("://", 1)[1].split("/")[0].split(":")[0]
    return f"Wi-Fi {hote}"


def ouvrir_camera(source, largeur, hauteur, fps):
    if not isinstance(source, int):
        # Flux réseau (ESP32-CAM) : la résolution se règle sur la caméra elle-même
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            return None
        ok, _ = cap.read()
        if not ok:
            cap.release()
            return None
        return cap
    index = source
    cap = cv2.VideoCapture(index, BACKEND)
    if not cap.isOpened():
        return None
    # MJPG d'abord : sinon beaucoup de caméras USB restent bloquées en basse résolution
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, largeur)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hauteur)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ok, _ = cap.read()
    if not ok:
        cap.release()
        return None
    return cap


def chercher_cameras(largeur, hauteur, fps, maxi=6):
    """Renvoie les numéros des caméras qui fonctionnent (0 à maxi-1)."""
    trouvees = []
    for i in range(maxi):
        cap = ouvrir_camera(i, largeur, hauteur, fps)
        if cap is None:
            continue
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"  caméra {i} : {w}x{h}")
        trouvees.append(i)
        cap.release()
    return trouvees


class LecteurCamera:
    """Lit une caméra dans un fil séparé et garde seulement la dernière image.

    Chaque caméra tourne ainsi à son propre rythme, sans attendre l'IA ni
    l'autre caméra, et l'IA prend toujours l'image la plus récente.
    """

    def __init__(self, cap, source=None):
        self.cap = cap
        self.source = source
        self.reconnexion = False
        self.image = None
        self.numero = 0
        self.temps = deque(maxlen=60)
        self.actif = True
        self.verrou = threading.Lock()
        threading.Thread(target=self._boucle, daemon=True).start()

    def _boucle(self):
        while self.actif:
            ok, image = self.cap.read()
            if not ok:
                if isinstance(self.source, str):
                    # Flux Wi-Fi coupé : on réessaie toutes les 2 s au lieu d'abandonner
                    self.reconnexion = True
                    self.cap.release()
                    time.sleep(2)
                    nouveau = cv2.VideoCapture(self.source)
                    if nouveau.isOpened():
                        self.cap = nouveau
                    continue
                self.actif = False
                break
            self.reconnexion = False
            with self.verrou:
                self.image = image
                self.numero += 1
                self.temps.append(time.perf_counter())

    def lire(self):
        with self.verrou:
            return self.image, self.numero

    def fps(self):
        t = list(self.temps)
        return (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 and t[-1] > t[0] else 0.0

    def arreter(self):
        self.actif = False
        time.sleep(0.1)
        self.cap.release()


class Camera:
    """Tout ce qui concerne une caméra : son flux, son modèle, ses statistiques."""

    def __init__(self, source, cap, modele):
        self.nom = nom_source(source)
        self.lecteur = LecteurCamera(cap, source)
        # Un modèle par caméra : en mode suivi, chaque caméra garde ses propres IDs
        self.model = YOLO(modele, task="detect")
        self.backend = cap.getBackendName()
        self.fps_annonce = cap.get(cv2.CAP_PROP_FPS)
        self.fourcc = fourcc_texte(cap.get(cv2.CAP_PROP_FOURCC))
        self.dernier_numero = 0
        self.n_traitees = 0
        self.temps_ia = deque(maxlen=30)
        self.temps_infer = deque(maxlen=30)
        self.mesures = {}
        self.resultat = None      # dernier résultat YOLO
        self.image = None         # dernière image brute analysée


# ---------------------------------------------------------------- mesures et affichage

def mesurer_image(image):
    """Mesure la qualité de l'image elle-même (sur une version réduite, pour aller vite)."""
    petite = cv2.resize(image, (320, 180), interpolation=cv2.INTER_AREA)
    gris = cv2.cvtColor(petite, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(petite, cv2.COLOR_BGR2HSV)
    return {
        "Luminosite": f"{gris.mean():.0f} / 255",
        "Contraste": f"{gris.std():.0f}",
        "Saturation": f"{hsv[..., 1].mean():.0f} / 255",
        "Nettete": f"{cv2.Laplacian(gris, cv2.CV_64F).var():.0f}",
        "Sur / sous-expose": f"{(gris >= 250).mean() * 100:.1f} % / {(gris <= 5).mean() * 100:.1f} %",
    }


def dessiner_panneau(img, lignes, x=0, y=0):
    """Panneau semi-transparent, une ligne par paramètre."""
    taille, epaisseur, interligne = 0.45, 1, 18
    largeur = max(cv2.getTextSize(l, cv2.FONT_HERSHEY_SIMPLEX, taille, epaisseur)[0][0]
                  for l in lignes) + 16
    hauteur = interligne * len(lignes) + 10
    zone = img[y:y + hauteur, x:x + largeur]
    zone[:] = (zone * 0.4).astype(np.uint8)
    for i, l in enumerate(lignes):
        couleur = (0, 255, 255) if l.startswith("--") else (255, 255, 255)
        cv2.putText(img, l, (x + 8, y + 17 + i * interligne), cv2.FONT_HERSHEY_SIMPLEX,
                    taille, couleur, epaisseur, cv2.LINE_AA)


def ajuster(image, largeur, hauteur):
    """Redimensionne sans déformer, avec des bandes noires si les formats diffèrent
    (ex. ESP32-CAM en 4:3 à côté de l'Action 4 en 16:9)."""
    h, w = image.shape[:2]
    echelle = min(largeur / w, hauteur / h)
    nw, nh = int(w * echelle), int(h * echelle)
    petite = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA if echelle < 1 else cv2.INTER_LINEAR)
    fond = np.zeros((hauteur, largeur, 3), np.uint8)
    x, y = (largeur - nw) // 2, (hauteur - nh) // 2
    fond[y:y + nh, x:x + nw] = petite
    return fond


def vue_camera(cam, largeur_vue, hauteur_vue, panneau, mode_suivi):
    """Construit l'image d'une caméra, à la taille de sa moitié d'écran."""
    if cam.resultat is None:
        vue = np.zeros((hauteur_vue, largeur_vue, 3), np.uint8)
        message = "En attente d'image..." if cam.lecteur.actif else "Camera deconnectee"
        cv2.putText(vue, f"Camera {cam.nom} : {message}", (20, hauteur_vue // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
        return vue

    vue = ajuster(cam.resultat.plot(), largeur_vue, hauteur_vue)

    if cam.lecteur.reconnexion:
        cv2.putText(vue, "FLUX COUPE - reconnexion...", (20, hauteur_vue - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
    elif not cam.lecteur.actif:
        cv2.putText(vue, "CAMERA DECONNECTEE", (20, hauteur_vue - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

    if panneau:
        h, w = cam.image.shape[:2]
        boites = cam.resultat.boxes
        fps_ia = ((len(cam.temps_ia) - 1) / (cam.temps_ia[-1] - cam.temps_ia[0])
                  if len(cam.temps_ia) > 1 else 0)
        infer = sum(cam.temps_infer) / len(cam.temps_infer) if cam.temps_infer else 0
        conf_max = f"{float(boites.conf.max()):.2f}" if len(boites) else "-"
        lignes = [
            f"-- CAMERA {cam.nom}  ({cam.backend})",
            f"Resolution : {w}x{h}   Codec : {cam.fourcc}",
            f"FPS annonce : {cam.fps_annonce:g}   FPS camera : {cam.lecteur.fps():.1f}",
            f"Image #{cam.lecteur.numero}",
            "-- IMAGE (mesuree)",
            *[f"{nom} : {v}" for nom, v in cam.mesures.items()],
            "-- IA",
            f"Inference : {infer:.0f} ms   FPS IA : {fps_ia:.1f}",
            f"Drones : {len(boites)}   conf max : {conf_max}",
        ]
        if mode_suivi:
            ids = ", ".join(str(int(i)) for i in boites.id) if boites.id is not None else "-"
            lignes.append(f"IDs : {ids}")
        dessiner_panneau(vue, lignes)
    return vue


def barre_globale(largeur, texte):
    """Bandeau en bas de la fenêtre avec les infos communes aux caméras."""
    barre = np.zeros((26, largeur, 3), np.uint8)
    cv2.putText(barre, texte, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (255, 255, 255), 1, cv2.LINE_AA)
    return barre


# ---------------------------------------------------------------- programme principal

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cams", nargs="+", default=None,
                   help="caméras : numéro USB ou adresse IP de l'ESP32, ex. --cams 1 192.168.1.42")
    p.add_argument("--nb", type=int, default=2, help="nombre de caméras en recherche auto")
    p.add_argument("--modele", default="best_1h.pt")
    p.add_argument("--conf", type=float, default=0.5, help="seuil de confiance YOLO")
    p.add_argument("--imgsz", type=int, default=640, help="taille d'image donnée à YOLO")
    p.add_argument("--largeur", type=int, default=1920, help="résolution demandée aux caméras")
    p.add_argument("--hauteur", type=int, default=1080)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--taille-vue", type=int, default=960,
                   help="largeur à l'écran de chaque caméra, en pixels")
    p.add_argument("--vertical", action="store_true", help="caméras empilées au lieu de côte à côte")
    p.add_argument("--track", action="store_true", help="suivi ByteTrack (un ID par drone)")
    args = p.parse_args()

    indexes = [lire_source(c) for c in args.cams] if args.cams else None
    if indexes is None:
        print("Recherche des caméras…")
        indexes = chercher_cameras(args.largeur, args.hauteur, args.fps)[:args.nb]
        if len(indexes) < args.nb:
            print(f"Seulement {len(indexes)} caméra(s) trouvée(s) sur {args.nb} demandée(s).")
            if not indexes:
                return

    cameras = []
    for i in indexes:
        cap = ouvrir_camera(i, args.largeur, args.hauteur, args.fps)
        if cap is None:
            print(f"Impossible d'ouvrir la caméra {nom_source(i)} ({i}) : elle est ignorée.")
            continue
        cam = Camera(i, cap, args.modele)
        print(f"Caméra {cam.nom} ouverte via {cam.backend} : "
              f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
              f" @ {cam.fps_annonce:g} fps, codec {cam.fourcc}")
        cameras.append(cam)
    if not cameras:
        print("Aucune caméra utilisable.")
        return

    try:
        import torch
        calcul = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "processeur (CPU)"
    except Exception:
        calcul = "?"
    print(f"Calcul de l'IA sur : {calcul}")
    print("\nq = quitter, h = panneaux, s = capture\n")

    largeur_vue = args.taille_vue
    hauteur_vue = largeur_vue * 9 // 16
    voir_panneau = True

    while True:
        nouvelle = False
        for cam in cameras:
            frame, numero = cam.lecteur.lire()
            if frame is None or numero == cam.dernier_numero:
                continue   # pas de nouvelle image pour cette caméra : on garde l'ancienne
            nouvelle = True
            cam.dernier_numero = numero
            cam.n_traitees += 1
            cam.temps_ia.append(time.perf_counter())

            t0 = time.perf_counter()
            if args.track:
                res = cam.model.track(frame, conf=args.conf, imgsz=args.imgsz, persist=True,
                                      tracker="bytetrack.yaml", verbose=False)[0]
            else:
                res = cam.model(frame, conf=args.conf, imgsz=args.imgsz, verbose=False)[0]
            cam.temps_infer.append((time.perf_counter() - t0) * 1000)
            cam.resultat, cam.image = res, frame
            if cam.n_traitees % 5 == 1:
                cam.mesures = mesurer_image(frame)

        if not nouvelle:
            if not any(c.lecteur.actif for c in cameras):
                print("Toutes les caméras sont déconnectées.")
                break
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        vues = [vue_camera(c, largeur_vue, hauteur_vue, voir_panneau, args.track) for c in cameras]
        ecran = np.vstack(vues) if args.vertical else np.hstack(vues)
        total = sum(len(c.resultat.boxes) for c in cameras if c.resultat is not None)
        texte = (f"{datetime.now():%H:%M:%S}   Modele : {args.modele}   Calcul : {calcul}   "
                 f"Mode : {'suivi' if args.track else 'detection'}   imgsz : {args.imgsz}   "
                 f"conf : {args.conf}   Drones (toutes cameras) : {total}")
        ecran = np.vstack([ecran, barre_globale(ecran.shape[1], texte)])

        cv2.imshow("MultiVisio - multi-cameras", ecran)
        touche = cv2.waitKey(1) & 0xFF
        if touche == ord("q"):
            break
        if touche == ord("h"):
            voir_panneau = not voir_panneau
        if touche == ord("s"):
            nom = f"capture_multi_{datetime.now():%Y%m%d_%H%M%S}.jpg"
            cv2.imwrite(nom, ecran)
            print(f"Capture enregistrée : {nom}")

    for cam in cameras:
        cam.lecteur.arreter()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
