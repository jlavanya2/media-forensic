import cv2
import numpy as np

def detect_watermark(path):

    img = cv2.imread(path)

    if img is None:
        return {"watermark_detected": False}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Simple brightness threshold detection
    bright_pixels = np.sum(gray > 240)
    total_pixels = gray.size

    ratio = bright_pixels / total_pixels

    if ratio > 0.05:
        return {"watermark_detected": True}
    else:
        return {"watermark_detected": False}