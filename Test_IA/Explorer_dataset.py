import cv2, random
from pathlib import Path

#Permet de parcourir le dataset
#Affiche 10 images au hasard avec les boîtes de détection (correction du dataset)

root = Path(r"C:\Users\Hades\Desktop\mv_dataset\seraphim")
imgs = [p for p in root.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]

for p in random.sample(imgs, 10):
    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    lab = next(root.rglob(p.stem + ".txt"), None)
    if lab:
        for l in lab.read_text().splitlines():
            _, x, y, bw, bh = map(float, l.split())
            x1, y1 = int((x - bw/2) * w), int((y - bh/2) * h)
            x2, y2 = int((x + bw/2) * w), int((y + bh/2) * h)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.imshow(p.name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()