"""Kalici ayarlar - goruntu, ses, oynanis.

Erisilebilirlik felsefesi (docs/menu-ui.md 5): **zorluk on ayari yok.**
"Kolay/Normal/Zor" secmiyorsun; mucadelenin hangi parcasini tutacagini
seciyorsun. Hicbir ayar "Kolay Mod" diye etiketlenmez, hicbir sey kilitlenmez.

Her ayar bir `Option` - degeri, secenekleri ve etiketleri birlikte tasir.
Boylece ayarlar ekrani listeyi gezerek kendini kurar; yeni bir ayar eklemek
tek satirlik is olur ve arayuz kodu hic degismez.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from src.systems.save import SETTINGS_NAME, user_data_dir


@dataclass
class Option:
    """Tek bir ayar: anahtar, etiket, degerler ve gosterilecek adlari."""

    key: str
    label: str
    values: tuple[Any, ...]
    labels: tuple[str, ...]
    default_index: int = 0
    note: str = ""                      # Ayarlar ekraninda alt aciklama

    def index_of(self, value: Any) -> int:
        try:
            return self.values.index(value)
        except ValueError:
            return self.default_index

    def label_for(self, value: Any) -> str:
        return self.labels[self.index_of(value)]


@dataclass
class Slider:
    """Surekli deger - ses seviyeleri ve parlaklik."""

    key: str
    label: str
    default: float = 1.0
    step: float = 0.05
    note: str = ""


# --- Sekme tanimlari --------------------------------------------------------
DISPLAY_OPTIONS: tuple[Option | Slider, ...] = (
    Option("fullscreen", "Tam ekran", (False, True), ("Pencere", "Tam ekran")),
    Option("scale", "Ölçek", (0, 2, 3, 4), ("Otomatik", "2×", "3×", "4×")),
    Option("screen_shake", "Ekran sarsıntısı", (0.0, 0.5, 1.0),
           ("Kapalı", "Az", "Normal"),
           default_index=2,
           note="Mide bulantısı yaşıyorsan kapatabilirsin."),
    Option("colorblind", "Renk körü modu",
           ("none", "protanopia", "deuteranopia", "tritanopia"),
           ("Yok", "Protanopi", "Döteranopi", "Tritanopi")),
    Option("ui_scale", "Arayüz boyutu", (1, 2), ("Normal", "Büyük")),
    Slider("brightness", "Parlaklık", default=1.0,
           note="Oyun karanlık - ekranına göre ayarla."),
)

AUDIO_OPTIONS: tuple[Option | Slider, ...] = (
    Slider("volume_master", "Ana ses", default=0.9),
    Slider("volume_music", "Müzik", default=0.6),
    Slider("volume_sfx", "Efektler", default=0.8),
    Slider("volume_echo", "Yankı fısıltıları", default=0.7,
           note="Ayrı kanal - rahatsız ediciyse kısabilirsin."),
)

GAMEPLAY_OPTIONS: tuple[Option | Slider, ...] = (
    Option("language", "Dil", ("tr", "en"), ("Türkçe", "English")),
    Option("damage_taken", "Alınan hasar", (0.5, 0.75, 1.0, 1.5),
           ("%50", "%75", "%100", "%150"), default_index=2),
    Option("enemy_speed", "Düşman hızı", (0.75, 1.0), ("%75", "%100"),
           default_index=1),
    Option("echo_penalty", "Yankı cezası", (True, False), ("Açık", "Kapalı"),
           note="Kapalıysa ölünce Yankı kademesi düşmez."),
    Option("auto_combo", "Otomatik combo", (False, True), ("Kapalı", "Açık"),
           note="Açıkken tek tuşla zincir devam eder."),
    Option("damage_numbers", "Hasar sayıları", (False, True),
           ("Kapalı", "Açık")),
    Option("rumble", "Kol titreşimi", (True, False), ("Açık", "Kapalı")),
)

TABS: tuple[tuple[str, tuple], ...] = (
    ("GÖRÜNTÜ", DISPLAY_OPTIONS),
    ("SES", AUDIO_OPTIONS),
    ("OYNANIŞ", GAMEPLAY_OPTIONS),
)

ALL_ENTRIES: tuple = DISPLAY_OPTIONS + AUDIO_OPTIONS + GAMEPLAY_OPTIONS


def _defaults() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for entry in ALL_ENTRIES:
        if isinstance(entry, Option):
            values[entry.key] = entry.values[entry.default_index]
        else:
            values[entry.key] = entry.default
    values["bindings"] = {}
    values["vsync"] = True
    return values


class Settings:
    """Ayar deposu. Her degisiklik aninda diske yazilir.

    "Kaydet" butonu yok: oyuncunun ayar yapip cikmasi kendi hatasi degildir.
    """

    def __init__(self) -> None:
        self._path = user_data_dir() / SETTINGS_NAME
        self._values: dict[str, Any] = _defaults()
        self._listeners: list[Callable[[str, Any], None]] = []
        self.load()

    # --- Erisim -------------------------------------------------------------
    def get(self, key: str, fallback: Any = None) -> Any:
        return self._values.get(key, fallback)

    def set(self, key: str, value: Any) -> None:
        if self._values.get(key) == value:
            return
        self._values[key] = value
        for listener in self._listeners:
            listener(key, value)
        self.save()

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def on_change(self, listener: Callable[[str, Any], None]) -> None:
        """Ayar degisince haberdar ol - tam ekran, ses, sarsinti icin."""
        self._listeners.append(listener)

    # --- Secenek gezinme ----------------------------------------------------
    def cycle(self, option: Option, direction: int) -> Any:
        """Secenegi ileri/geri kaydir ve yeni degeri doner."""
        index = option.index_of(self.get(option.key))
        index = (index + direction) % len(option.values)
        value = option.values[index]
        self.set(option.key, value)
        return value

    def adjust(self, slider: Slider, direction: int) -> float:
        value = float(self.get(slider.key, slider.default))
        value = max(0.0, min(1.0, value + direction * slider.step))
        self.set(slider.key, round(value, 3))
        return value

    def reset_to_defaults(self) -> None:
        for key, value in _defaults().items():
            self.set(key, value)

    # --- Kalicilik ----------------------------------------------------------
    def load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return          # Ilk calistirma ya da bozuk dosya - varsayilanlar
        if not isinstance(raw, dict):
            return
        for key in self._values:
            if key in raw:
                self._values[key] = raw[key]

    def save(self) -> None:
        try:
            self._path.write_text(
                json.dumps(self._values, indent=2, ensure_ascii=False),
                encoding="utf-8")
        except OSError as exc:
            print(f"[settings] kaydedilemedi: {exc}")

    def as_dict(self) -> dict[str, Any]:
        return dict(self._values)
