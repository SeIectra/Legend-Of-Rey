"""Tek bir animasyonu buyuk olcekte, hucre sinirlari gorunur halde basar."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
pygame.display.set_mode((64, 64))

from lore.gfx.sprites import ARCHETYPES, build_animation
from lore.gfx.text import draw_text

name = os.environ.get("NAME", "rey_armed")
state = os.environ.get("STATE", "run")
zoom = int(os.environ.get("ZOOM", "7"))

spec = ARCHETYPES[name]
frames = build_animation(spec, state)

pad = 6
cw, ch = spec.cell_w * zoom, spec.cell_h * zoom
sheet = pygame.Surface((pad + len(frames) * (cw + pad), ch + pad * 2 + 14))
sheet.fill((26, 24, 36))
draw_text(sheet, f"{name} / {state}  hucre {spec.cell_w}x{spec.cell_h}", 4, 3,
          color=(235, 205, 120))

x = pad
for i, frame in enumerate(frames):
    big = pygame.transform.scale(frame, (cw, ch))
    pygame.draw.rect(sheet, (38, 36, 52), (x, pad + 14, cw, ch))
    sheet.blit(big, (x, pad + 14))
    # Hucre cercevesi: tasma var mi gorelim
    pygame.draw.rect(sheet, (90, 70, 120), (x, pad + 14, cw, ch), 1)
    # Taban cizgisi
    fy = pad + 14 + spec.foot_y * zoom
    pygame.draw.line(sheet, (120, 90, 60), (x, fy), (x + cw, fy), 1)
    x += cw + pad

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "testshots")
os.makedirs(out_dir, exist_ok=True)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(out_dir, "zoom.png")
pygame.image.save(sheet, out)
print(f"{out} -> {sheet.get_width()}x{sheet.get_height()}")
