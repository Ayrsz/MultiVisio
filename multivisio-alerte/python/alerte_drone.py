"""Envoie une alerte à l'appli Android quand un drone est détecté.

Utilise Firebase Cloud Messaging (FCM) : le PC envoie le message à Google,
qui le livre à tous les téléphones abonnés au sujet "drones".

Il faut le fichier de clé "cle-firebase.json" (voir GUIDE.md, étape 5)
dans le même dossier que ce script. Ne jamais le mettre sur GitHub.
"""

import time
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging

SUJET = "drones"            # doit être le même que dans Notifications.kt
DELAI_ENTRE_ALERTES = 30    # secondes : évite d'envoyer 30 alertes par seconde
CLE = Path(__file__).with_name("cle-firebase.json")

_derniere_alerte = 0.0


def _connexion():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(str(CLE)))


def envoyer_alerte(confiance, camera="ESP32-CAM", forcer=False):
    """Envoie l'alerte. Renvoie True si elle est partie, False si on attend encore.

    confiance : nombre entre 0 et 1 donné par YOLO (ex : 0.87).
    """
    global _derniere_alerte
    maintenant = time.time()
    if not forcer and maintenant - _derniere_alerte < DELAI_ENTRE_ALERTES:
        return False

    _connexion()
    message = messaging.Message(
        topic=SUJET,
        # Message "data" : c'est l'appli qui construit la notification
        data={
            "confiance": str(round(confiance * 100)),
            "heure": datetime.now().strftime("%H:%M:%S"),
            "camera": camera,
        },
        # Priorité haute : le téléphone se réveille tout de suite
        android=messaging.AndroidConfig(priority="high"),
    )
    messaging.send(message)
    _derniere_alerte = maintenant
    print(f"Alerte envoyée ({round(confiance * 100)} %)")
    return True
