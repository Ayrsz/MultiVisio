# Comparatif des datasets de drones pour YOLO

6 octobre 2026 · Loulou ([version éditable](https://claude.ai/code/artifact/8606f1c1-2d51-4bcb-bbca-058dc0c6154f))

## Recommandation

Partir du **Seraphim Drone Detection Dataset** : 83 483 images RGB déjà au format YOLO, licence CC BY 4.0, utilisable tel quel avec Ultralytics. C'est le seul candidat qui combine grande taille, format natif YOLO et licence claire.

Le compléter ensuite avec le **Drone Detection Dataset de Svanström** (CC0) pour ses oiseaux, avions et hélicoptères annotés : ce sont les faux positifs typiques d'une caméra au sol. **Anti-UAV** sert de banc d'essai pour les cibles minuscules et l'infrarouge, si MultiVisio utilise une caméra thermique.

Caméra du projet : une ESP32-CAM, en général équipée d'un capteur OV2640 RGB (2 MP, 1600×1200 au maximum, flux JPEG souvent réduit à 640×480 ou moins). Le choix d'un dataset RGB tient donc. Conséquence : à cette résolution, un drone à quelques dizaines de mètres ne fait que quelques pixels, ce qui rend les cibles petites et les distracteurs (oiseaux) encore plus importants.

## Tableau comparatif

| Dataset | Taille | Licence | Annotation | Prise de vue | Prêt pour YOLO |
| --- | --- | --- | --- | --- | --- |
| [Seraphim](https://github.com/Seraphim-Defence-Systems/seraphim-drone-detection-dataset) | 83 483 images (75 134 train, 8 349 test) | CC BY 4.0 | YOLO, 640×640, 1 classe | RGB, agrégé de 23 datasets ouverts, surtout multirotors | Oui, tel quel |
| [Svanström Drone Detection](https://github.com/DroneDetectionThesis/Drone-detection-dataset) | 650 vidéos, 203 328 images annotées | CC0 1.0 | MATLAB .mat, 4 classes (drone, oiseau, avion, hélico) | Visible (285 vidéos) + IR (365), depuis le sol, plus audio | Non, conversion .mat vers YOLO |
| [Anti-UAV](https://github.com/ZhaoJ9014/Anti-UAV) (300 / 410 / 600) | 300 : 318 paires de vidéos RGB-IR, plus de 580 000 boîtes | MIT (dépôt) | Boîtes par image au format suivi (JSON) | Full HD, cibles minuscules, fonds nuages, bâtiments, montagne, mer ; 410 et 600 en IR seul | Non, extraction des images + conversion |
| [Det-Fly](https://github.com/Jake-WU/Det-Fly) | Plus de 13 000 images | MIT (dépôt) | Fichiers d'annotation séparés | Air-air depuis un DJI Mavic 2 ; fonds ciel, ville, champ, montagne ; moitié des cibles sous 5 % de l'image | Non, conversion |
| [DUT Anti-UAV](https://github.com/wangdongdut/DUT-Anti-UAV) | Détection + 20 séquences de suivi | Apache-2.0 (dépôt) | VOC XML | RGB depuis le sol, plusieurs modèles de drones | Non, conversion |
| [Pawełczyk & Wojtyra](https://github.com/Maciullo/DroneDetectionDataset) | 51 446 train + 5 375 test, 640×480 | MIT pour les étiquettes ; images tirées de vidéos YouTube | XML pour Haar Cascade | RGB, environnements et heures variés | Non, conversion |
| [Roboflow Universe](https://universe.roboflow.com/ivonne/yolo-drone-detection-dataset) (petits jeux) | Souvent quelques centaines d'images (ex. 253) | Variable, souvent CC BY 4.0 | Export YOLO direct | Très hétérogène, qualité inégale | Oui |

Sources consultées le 6 octobre 2026. Pour Anti-UAV, Det-Fly et DUT, la licence indiquée est celle du dépôt GitHub ; les données elles-mêmes sont publiées pour la recherche et une vérification est à faire avant tout usage commercial. Le format DUT (VOC XML) est déduit de l'article, pas lu dans le dépôt.

## Forces et limites

- **Seraphim** : volume et format imbattables. Limite : agrégat de 23 sources, donc doublons possibles entre train et test et licences d'origine à vérifier source par source. Pas de classe « oiseau » pour apprendre les faux positifs.
- **Svanström** : seule licence CC0 et seul jeu avec des distracteurs annotés (oiseaux, avions, hélicoptères). Limite : vidéos en basse résolution et images consécutives très redondantes ; il faut sous-échantillonner.
- **Anti-UAV** : référence académique pour les cibles très petites et l'IR. Limite : conçu pour le suivi d'un seul drone par vidéo, donc conversion nécessaire et peu de variété de scènes par image.
- **Det-Fly** : utile seulement si la caméra est elle-même en vol ; un seul modèle de drone cible.
- **DUT Anti-UAV** : bon jeu de test RGB indépendant, à garder hors de l'entraînement pour mesurer la généralisation.
- **Pawełczyk & Wojtyra** : gros volume, mais images issues de YouTube : droits flous, à éviter hors usage de recherche.
- **Roboflow Universe** : pratique pour un premier test en quelques minutes, trop petit et trop hétérogène pour un modèle sérieux.

## Plan avec YOLO Ultralytics

1. Télécharger Seraphim, écrire un `data.yaml` (1 classe `drone`) et entraîner une première base, par exemple `yolo detect train model=yolo11n.pt data=data.yaml imgsz=640`.
2. Mesurer le mAP sur un jeu de test externe (DUT Anti-UAV ou quelques séquences Anti-UAV converties) pour vérifier que le modèle ne sur-apprend pas les sources de Seraphim.
3. Convertir Svanström (.mat vers YOLO avec le décodeur Python fourni), sous-échantillonner les vidéos, puis ajouter les oiseaux, avions et hélicoptères comme classes ou comme images négatives.
4. Si les drones sont très petits dans l'image, tester `imgsz=1280` ou un découpage en tuiles avant de changer de dataset.
5. Ajouter quelques centaines d'images filmées avec la caméra réelle de MultiVisio dès qu'elle est choisie : c'est ce qui comble le mieux l'écart avec le terrain.

Avec l'ESP32-CAM, l'inférence YOLO ne tournera pas sur la carte elle-même : la carte envoie le flux vidéo (Wi-Fi) et un PC fait la détection. Le capteur exact (OV2640 ou autre) reste à confirmer ; s'il s'agissait d'un capteur thermique, Anti-UAV 410/600 deviendrait la base à la place de Seraphim.
