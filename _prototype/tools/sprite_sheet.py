"""Tum arketiplerin animasyon karelerini tek bir kontakt sayfasina basar."""
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

STATES = ["idle", "run", "jump", "fall", "attack1", "attack2", "attack3",
          "dash", "hurt", "death"]
ZOOM = 3
PAD = 4
LABEL_W = 70

ONLY = [n for n in (os.environ.get("ONLY") or "").split(",") if n]
STATES = [s for s in (os.environ.get("STATES") or ",".join(STATES)).split(",") if s]
rows = []
for name, spec in ARCHETYPES.items():
    if ONLY and name not in ONLY:
        continue
    for state in STATES:
        rows.append((name, state, build_animation(spec, state)))

cell_w = max(s.cell_w for s in ARCHETYPES.values())
cell_h = max(s.cell_h for s in ARCHETYPES.values())
max_frames = max(len(f) for _, _, f in rows)

sheet_w = LABEL_W + max_frames * (cell_w * ZOOM + PAD) + PAD
sheet_h = PAD + len(rows) * (cell_h * ZOOM + PAD)
sheet = pygame.Surface((sheet_w, sheet_h), pygame.SRCALPHA)
sheet.fill((22, 20, 32))

y = PAD
for name, state, frames in rows:
    draw_text(sheet, f"{name}", 3, y + 4, color=(230, 200, 120))
    draw_text(sheet, f"{state}", 3, y + 16, color=(140, 150, 175))
    x = LABEL_W
    for frame in frames:
        big = pygame.transform.scale(
            frame, (frame.get_width() * ZOOM, frame.get_height() * ZOOM))
        pygame.draw.rect(sheet, (34, 32, 48),
                         (x, y, big.get_width(), big.get_height()))
        sheet.blit(big, (x, y))
        x += big.get_width() + PAD
    y += cell_h * ZOOM + PAD

out_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "testshots")
os.makedirs(out_dir, exist_ok=True)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(out_dir, "sprites.png")
pygame.image.save(sheet, out)
print(f"{out} -> {sheet_w}x{sheet_h}, {len(rows)} satir")
