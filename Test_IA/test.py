from ultralytics import YOLO
import random
from pathlib import Path

model = YOLO("best_1h.pt")
imgs = list(Path("seraphim/test/images").rglob("*.jpg"))
for p in random.sample(imgs, 8):
    model(str(p), conf=0.5)[0].show()