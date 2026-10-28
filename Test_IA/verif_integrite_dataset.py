from pathlib import Path

#Permet de vérifier l'intégrité du dataset (ie si toutes les images ont des labels ect...)

root = Path("seraphim")
exts = {".jpg", ".jpeg", ".png"}

images = [p for p in root.rglob("*") if p.suffix.lower() in exts]
labels = {p.stem: p for p in root.rglob("*.txt")}
print(f"{len(images)} images, {len(labels)} fichiers txt")

sans_label = [p for p in images if p.stem not in labels]
print(f"{len(sans_label)} images sans fichier label")

mauvais = 0
classes = set()
for p in labels.values():
    for ligne in p.read_text().splitlines():
        v = ligne.split()
        if not v:
            continue
        classes.add(v[0])
        if len(v) != 5 or not all(0 <= float(x) <= 1 for x in v[1:]):
            mauvais += 1
print(f"Classes trouvées : {classes}  (attendu : {{'0'}})")
print(f"{mauvais} lignes mal formées")