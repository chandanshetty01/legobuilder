#!/usr/bin/env python3
"""Convert a grayscale height/detail map into a correct tangent-space normal map.

AI image models can't reliably produce a physically-valid normal map (the precise
blue/purple encoding), so we have gpt-image-2 make a grayscale surface heightmap
and derive the normal map here with a Sobel gradient. Tiling is preserved with
wrap-around (np.roll), so the result stays seamless.

  python3 height2normal.py textures/plastic_surface.png textures/plastic_normal.png [strength]
"""
import sys
import numpy as np
from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "textures/plastic_surface.png"
dst = sys.argv[2] if len(sys.argv) > 2 else "textures/plastic_normal.png"
strength = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0

h = np.asarray(Image.open(src).convert("L"), dtype=np.float32) / 255.0

# central-difference gradients with wrap (seamless); +x right, +y down
dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5

nx = -dx * strength
ny = -dy * strength            # image +y is down; flip later for GL (+Y up) convention
nz = np.ones_like(h)
ln = np.sqrt(nx * nx + ny * ny + nz * nz)
nx, ny, nz = nx / ln, ny / ln, nz / ln

rgb = np.zeros((*h.shape, 3), dtype=np.uint8)
rgb[..., 0] = np.clip((nx * 0.5 + 0.5) * 255, 0, 255)
rgb[..., 1] = np.clip(((-ny) * 0.5 + 0.5) * 255, 0, 255)   # GL-style green (Y up)
rgb[..., 2] = np.clip((nz * 0.5 + 0.5) * 255, 0, 255)

Image.fromarray(rgb, "RGB").save(dst)
m = rgb.reshape(-1, 3).mean(0)
print(f"wrote {dst}  mean RGB={m[0]:.0f},{m[1]:.0f},{m[2]:.0f} (flat ~128,128,255)")
