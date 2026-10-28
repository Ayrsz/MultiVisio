from ultralytics import YOLO
import random
from pathlib import Path

#Sort 8 images au hasard dans le dataset et les affiche avec les boîtes de détection
#On choisit le modèle que l'on veut tester ici best_1h.pt

model = YOLO("best_1h.pt")
imgs = list(Path(r"C:\Users\Hades\Desktop\mv_dataset\seraphim\test\images").rglob("*.jpg"))
for p in random.sample(imgs, 8):
    model(str(p), conf=0.5)[0].show()