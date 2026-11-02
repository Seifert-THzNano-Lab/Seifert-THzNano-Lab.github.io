"""Bloom + vignette post-processing for the renders. usage: post.py in.png out.jpg [out_w]"""
import sys
import numpy as np
from PIL import Image, ImageFilter

src, dst = sys.argv[1], sys.argv[2]
out_w = int(sys.argv[3]) if len(sys.argv) > 3 else None
im = Image.open(src)
a = np.asarray(im).astype(np.float32)
a = a / (65535.0 if a.max() > 255 else 255.0)
a = a[..., :3]
lin = a ** 2.2
lum = lin @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
th = float(sys.argv[4]) if len(sys.argv) > 4 else 0.45
mask = np.clip((lum - th) / (1 - th), 0, 1)[..., None]
bright = lin * mask
H, W = lum.shape
bloom = np.zeros_like(lin)
for rad, w in [(W * 0.004, 0.55), (W * 0.012, 0.45), (W * 0.035, 0.35)]:
    b = np.stack([np.asarray(Image.fromarray((bright[..., c] * 255).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad))).astype(np.float32) / 255 for c in range(3)], -1)
    bloom += w * b
out = lin + bloom
# soft vignette
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
vig = 1 - (float(sys.argv[5]) if len(sys.argv) > 5 else 0.28) * np.clip(r - 0.55, 0, 1) ** 1.5
out = out * vig[..., None]
out = np.clip(out, 0, 1) ** (1 / 2.2)
img = Image.fromarray((out * 255 + 0.5).astype(np.uint8))
if out_w:
    img = img.resize((out_w, round(out_w * H / W)), Image.LANCZOS)
img.save(dst, quality=92)
