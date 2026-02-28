import cv2
import numpy as np

def analyze_image(path):

    img = cv2.imread(path)

    if img is None:
        return {
            "width": 0,
            "height": 0,
            "edge_density": 0,
            "entropy": 0,
            "suspicious_region": None
        }

    # Resize large images for performance
    if img.shape[1] > 1200:
        img = cv2.resize(img, (800, 600))

    height, width = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 100, 200)
    edge_density = float(np.sum(edges)) / (width * height * 255)

    hist = cv2.calcHist([gray],[0],None,[256],[0,256])
    hist_norm = hist.ravel() / hist.sum()
    entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-7))

    if entropy < 4:
        suspicious_region = {
            "x": int(width * 0.3),
            "y": int(height * 0.3),
            "w": int(width * 0.4),
            "h": int(height * 0.4)
        }
    else:
        suspicious_region = None

    return {
        "width": width,
        "height": height,
        "edge_density": round(float(edge_density),4),
        "entropy": round(float(entropy),2),
        "suspicious_region": suspicious_region
    }