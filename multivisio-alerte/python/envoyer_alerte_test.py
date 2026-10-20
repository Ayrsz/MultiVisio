"""Envoie UNE fausse alerte pour tester l'appli, sans caméra ni IA.

Lancer :  python envoyer_alerte_test.py
"""

from alerte_drone import envoyer_alerte

envoyer_alerte(confiance=0.99, camera="test", forcer=True)
