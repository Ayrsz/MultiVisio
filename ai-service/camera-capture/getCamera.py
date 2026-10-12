import cv2
import numpy as np


URL = "http://10.51.54.130:81/stream"
cam = cv2.VideoCapture(URL)


def getImage() :
    read = 1
    read, image = cam.read()
    while (read):
        cv2.imshow("Image", image)
        read, image = cam.read()
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    cam.release()
    cv2.destroyAllWindows()
    

if __name__ == "__main__":
    getImage()
   