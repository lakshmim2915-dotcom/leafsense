"""Step 1: segment the plant (Excess Green) and extract per-photo features."""
import cv2
import numpy as np

FEATURE_NAMES = ["green_area_px", "green_area_pct", "mean_R", "mean_G", "mean_B",
                 "mean_H", "mean_S", "mean_V", "exg_mean", "greenness_ratio",
                 "yellow_pct"]

def segment_plant(bgr):
    """Excess Green index ExG = 2g - r - b on normalised channels, Otsu threshold."""
    img = bgr.astype(np.float32)
    total = img.sum(axis=2) + 1e-6
    b, g, r = img[..., 0] / total, img[..., 1] / total, img[..., 2] / total
    exg = 2 * g - r - b
    exg8 = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(exg8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return mask > 0, exg

def extract_features(path):
    bgr = cv2.imread(path)
    if bgr is None:
        raise ValueError(f"Cannot read image: {path}")
    bgr = cv2.resize(bgr, (640, 480))
    mask, exg = segment_plant(bgr)
    n = int(mask.sum())
    if n == 0:
        return dict.fromkeys(FEATURE_NAMES, 0.0)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    px_bgr, px_hsv = bgr[mask], hsv[mask]
    yellow = ((px_hsv[:, 0] >= 15) & (px_hsv[:, 0] <= 35)).mean() * 100
    mB, mG, mR = px_bgr.mean(axis=0)
    return {
        "green_area_px": n,
        "green_area_pct": 100 * n / mask.size,
        "mean_R": mR, "mean_G": mG, "mean_B": mB,
        "mean_H": px_hsv[:, 0].mean(), "mean_S": px_hsv[:, 1].mean(),
        "mean_V": px_hsv[:, 2].mean(),
        "exg_mean": float(exg[mask].mean()),
        "greenness_ratio": mG / (mR + mB + 1e-6),
        "yellow_pct": yellow,
    }

if __name__ == "__main__":
    import sys, json
    print(json.dumps(extract_features(sys.argv[1]), indent=2, default=float))
