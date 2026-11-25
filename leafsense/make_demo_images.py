"""Creates fake plant photos so you can test the app before you have real data.
Run:  python make_demo_images.py   -> folder demo_images/ (Control, Stressed)"""
import os, cv2, numpy as np
rng = np.random.default_rng(1)
for name, stressed in [("Control", False), ("Stressed", True)]:
    os.makedirs(f"demo_images/{name}", exist_ok=True)
    for day in range(14):
        img = np.full((480, 640, 3), (215, 220, 225), np.uint8)
        cv2.rectangle(img, (0, 400), (640, 480), (90, 110, 130), -1)          # soil/table
        s = max(0, day - 6) if stressed else 0                                 # stress starts day 7
        radius = int(60 + 3 * day - (4 * s if stressed else 0))
        green = (45, int(165 - 9 * s), int(50 + 14 * s))                       # BGR: green -> yellow
        for ang in range(0, 360, 45):
            cx = int(320 + radius * 0.6 * np.cos(np.radians(ang)))
            cy = int(250 + radius * 0.6 * np.sin(np.radians(ang)))
            cv2.ellipse(img, (cx, cy), (radius // 2, radius // 4), ang, 0, 360, green, -1)
        img = cv2.add(img, rng.integers(0, 6, img.shape, dtype=np.uint8))
        cv2.imwrite(f"demo_images/{name}/day{day+1:02d}.jpg", img)
print("Done. Upload day01..day14 for each plant in the app.")
