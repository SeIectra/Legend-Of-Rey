"""LORE paleti.

Prosedurel sanatin tutarli gorunmesinin tek sirri sinirli bir palettir. Oyundaki
her piksel buradaki rampalardan birinden gelir; hicbir yerde "elle" renk
yazilmaz. Bir Act'in atmosferini degistirmek istedigimizde tek yapmamiz gereken
o Act'in `grade` degerlerini degistirmek.

Her rampa 5 basamak: 0 = en koyu (govde golgesi), 4 = en acik (isik vurgusu).
Sprite'lar rampa *indeksi* ile cizilir, renk degil - boylece ayni sprite farkli
rampalarla yeniden renklendirilebilir (ornegin ayni goblin, Act IV'te kul
renginde).
"""
from __future__ import annotations

Color = tuple[int, int, int]

# --- Rampalar ---------------------------------------------------------------
RAMPS: dict[str, tuple[Color, ...]] = {
    # Karanlik, cerceve, golge
    "ink":    ((6, 5, 11), (13, 12, 22), (24, 21, 38), (38, 34, 56), (56, 51, 76)),
    # Tas, kale, zindan
    "stone":  ((28, 30, 42), (48, 52, 68), (72, 78, 96), (104, 110, 128), (146, 152, 170)),
    # Toprak, tahta, kok
    "earth":  ((32, 22, 20), (56, 38, 30), (86, 58, 42), (122, 84, 56), (162, 118, 78)),
    # Yosun, yaprak, orman
    "moss":   ((16, 32, 26), (28, 56, 40), (46, 88, 56), (74, 126, 74), (118, 168, 98)),
    # Ates, kor, Rey'in vurgu rengi
    "ember":  ((58, 16, 18), (108, 30, 26), (168, 58, 32), (222, 108, 44), (255, 176, 88)),
    # Su, buz, Essence
    "azure":  ((14, 30, 54), (22, 54, 92), (34, 92, 142), (62, 140, 190), (126, 200, 236)),
    # Yanki, buyu, dusman auras
    "violet": ((30, 16, 48), (52, 28, 82), (84, 46, 124), (126, 78, 174), (176, 132, 220)),
    # Ten
    "flesh":  ((62, 34, 30), (104, 62, 48), (152, 100, 74), (198, 146, 110), (232, 190, 156)),
    # Altin, hazine, UI vurgusu
    "gold":   ((70, 44, 12), (118, 78, 20), (176, 128, 34), (224, 180, 60), (255, 226, 132)),
    # Kul, sis, Act IV
    "ash":    ((26, 24, 28), (52, 48, 54), (84, 80, 88), (126, 122, 130), (176, 172, 180)),
    # Kan, hasar
    "blood":  ((46, 8, 12), (88, 14, 20), (140, 24, 30), (190, 44, 48), (232, 92, 88)),
    # Kemik, kafatasi
    "bone":   ((72, 68, 58), (110, 104, 88), (152, 146, 124), (196, 190, 168), (236, 232, 214)),
}

# --- Anlamsal takma adlar ---------------------------------------------------
BLACK: Color = (0, 0, 0)
WHITE: Color = (245, 244, 250)
TRANSPARENT: Color = (255, 0, 255)      # Colorkey olarak kullanilan renk

UI_BG: Color = RAMPS["ink"][1]
UI_PANEL: Color = RAMPS["ink"][2]
UI_BORDER: Color = RAMPS["gold"][2]
UI_TEXT: Color = RAMPS["bone"][4]
UI_TEXT_DIM: Color = RAMPS["stone"][3]
UI_TEXT_HILITE: Color = RAMPS["gold"][4]
UI_SHADOW: Color = RAMPS["ink"][0]

HEALTH: Color = RAMPS["blood"][3]
HEALTH_BG: Color = RAMPS["ink"][2]
ESSENCE: Color = RAMPS["azure"][3]
MANA: Color = RAMPS["violet"][3]

DAMAGE_FLASH: Color = (255, 240, 240)
HEAL_FLASH: Color = (180, 255, 200)


def ramp(name: str, step: int) -> Color:
    """Rampadan renk al. Indeks tasarsa uca kirpilir."""
    colors = RAMPS.get(name, RAMPS["stone"])
    return colors[max(0, min(step, len(colors) - 1))]


def shade(color: Color, amount: float) -> Color:
    """Rengi koyulastir (amount<0) veya aydinlat (amount>0). -1..1 arasi."""
    if amount >= 0:
        return (
            int(color[0] + (255 - color[0]) * amount),
            int(color[1] + (255 - color[1]) * amount),
            int(color[2] + (255 - color[2]) * amount),
        )
    k = 1.0 + amount
    return (int(color[0] * k), int(color[1] * k), int(color[2] * k))


def mix(a: Color, b: Color, t: float) -> Color:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def with_alpha(color: Color, alpha: int) -> tuple[int, int, int, int]:
    return (color[0], color[1], color[2], max(0, min(255, alpha)))


def luminance(color: Color) -> float:
    """Algilanan parlaklik (0..1). Kontrast kararlari icin."""
    r, g, b = (c / 255.0 for c in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_on(background: Color) -> Color:
    """Verilen arka planda okunur bir metin rengi sec."""
    return RAMPS["ink"][0] if luminance(background) > 0.5 else UI_TEXT


# --- Act renk derecelendirmesi ----------------------------------------------
# Her Act'in kendi atmosferi var. Bu degerler postfx tarafindan tum kareye
# uygulanir; sprite'lari yeniden uretmeye gerek kalmaz.
ACT_GRADES: dict[int, dict] = {
    1: {"tint": (46, 52, 78), "tint_strength": 0.14, "saturation": 0.92,
        "vignette": 0.35, "name": "The Waking Hollow"},
    2: {"tint": (60, 74, 44), "tint_strength": 0.12, "saturation": 1.05,
        "vignette": 0.28, "name": "Emberfall Woods"},
    3: {"tint": (26, 62, 96), "tint_strength": 0.22, "saturation": 0.88,
        "vignette": 0.42, "name": "The Drowned Vault"},
    4: {"tint": (78, 62, 58), "tint_strength": 0.20, "saturation": 0.80,
        "vignette": 0.46, "name": "The Ashen Spire"},
    5: {"tint": (74, 44, 104), "tint_strength": 0.24, "saturation": 1.10,
        "vignette": 0.50, "name": "Echo of the Sundering"},
}


def act_grade(act: int) -> dict:
    return ACT_GRADES.get(act, ACT_GRADES[1])
