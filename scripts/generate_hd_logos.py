#!/usr/bin/env python3
from PIL import Image
import numpy as np

src = Image.open("design-src/new_logo.jpg")
arr = np.array(src)

# Crop to content with some padding
gray = np.mean(arr, axis=2)
mask = gray < 240
rows = np.any(mask, axis=1)
cols = np.any(mask, axis=0)
rmin, rmax = np.where(rows)[0][[0, -1]]
cmin, cmax = np.where(cols)[0][[0, -1]]

# Add 20px padding
pad = 20
rmin = max(0, rmin - pad)
rmax = min(arr.shape[0]-1, rmax + pad)
cmin = max(0, cmin - pad)
cmax = min(arr.shape[1]-1, cmax + pad)

cropped = src.crop((cmin, rmin, cmax+1, rmax+1))
print(f"Cropped: {cropped.size}")

# Convert white bg to transparent
arr_c = np.array(cropped.convert("RGBA"))
# White pixels (all channels > 245) become transparent
white_mask = np.all(arr_c[:,:,:3] > 245, axis=2)
arr_c[white_mask, 3] = 0
# Near-white pixels get partial transparency for anti-aliasing
near_white = np.all(arr_c[:,:,:3] > 230, axis=2) & ~white_mask
darkness = 255 - np.min(arr_c[:,:,:3], axis=2)
arr_c[near_white, 3] = np.clip(darkness[near_white] * 10, 0, 255).astype(np.uint8)

result = Image.fromarray(arr_c)

# Generate HD PNGs for each density bucket
base = "menu-ocr-android/app/src/main/res"
sizes = {
    "drawable": 512,
    "drawable-hdpi": 768,
    "drawable-xhdpi": 1024,
    "drawable-xxhdpi": 1280,
}

for folder, width in sizes.items():
    aspect = result.size[1] / result.size[0]
    height = int(width * aspect)
    resized = result.resize((width, height), Image.LANCZOS)
    path = f"{base}/{folder}/ic_splash_logo.png"
    resized.save(path)
    print(f"Saved {path}: {resized.size}")

print("Done!")
