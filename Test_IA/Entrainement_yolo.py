from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolo11n.pt")
    model.train(
        data="data.yaml",
        epochs=1,
        imgsz=640,
        batch=8,        # 4 si "CUDA out of memory"
        device=0,
        workers=2,      # 0 si erreurs sous Windows
        fraction=0.1,   # ~8 000 images pour un premier essai
        cache=False,    # n'essayez pas de tout charger en RAM
    )