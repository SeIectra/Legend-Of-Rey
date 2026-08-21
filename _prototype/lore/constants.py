"""LORE - Legend of Rey: Echoes -- global sabitler.

Buradaki her sayi oyunun "hissini" belirler. Degistirirken kucuk adimlarla
ilerle: bu dosyadaki bir satir 28 bolumun tamamini etkiler.
"""
from __future__ import annotations

# --- Kimlik -----------------------------------------------------------------
GAME_TITLE = "LORE - Legend Of Rey: Echoes"
GAME_SHORT = "LORE"
GAME_VERSION = "0.1.0"
SAVE_DIR_NAME = "LegendOfReyEchoes"

# --- Zamanlama --------------------------------------------------------------
# Sabit zaman adimi: fizik makinenin hizindan bagimsiz, deterministik calisir.
TICK_RATE = 60
FIXED_DT = 1.0 / TICK_RATE
MAX_FRAME_SKIP = 5          # Bir karede en fazla bu kadar tick yakalanir
                            # (yoksa lag sonrasi "olum sarmali" olusur)

# --- Cozunurluk -------------------------------------------------------------
# Sanal cozunurlukte cizip tam sayi katiyla olcekliyoruz: pixel art keskin kalir.
VIRTUAL_W = 480
VIRTUAL_H = 270
DEFAULT_SCALE = 4                       # 1920x1080
WINDOW_W = VIRTUAL_W * DEFAULT_SCALE
WINDOW_H = VIRTUAL_H * DEFAULT_SCALE

# --- Dunya olcegi -----------------------------------------------------------
TILE = 16                   # Bir tile kac sanal piksel
CHUNK = 16                  # Tilemap parcalama boyutu (tile cinsinden)

# --- Fizik ------------------------------------------------------------------
GRAVITY = 780.0             # px/s^2
MAX_FALL_SPEED = 420.0
TERMINAL_FALL_SPEED = 560.0 # Dash/knockback sonrasi tavan

# --- Katmanlar (cizim sirasi) ----------------------------------------------
LAYER_SKY = 0
LAYER_PARALLAX = 10
LAYER_BG_TILES = 20
LAYER_PROPS_BACK = 30
LAYER_ENTITIES = 40
LAYER_TILES = 50
LAYER_PROPS_FRONT = 60
LAYER_PARTICLES = 70
LAYER_FOREGROUND = 80
LAYER_UI = 90

# --- Carpisma maskeleri -----------------------------------------------------
MASK_NONE = 0
MASK_PLAYER = 1 << 0
MASK_ENEMY = 1 << 1
MASK_PLAYER_ATTACK = 1 << 2
MASK_ENEMY_ATTACK = 1 << 3
MASK_PICKUP = 1 << 4
MASK_TRIGGER = 1 << 5
MASK_SOLID = 1 << 6
