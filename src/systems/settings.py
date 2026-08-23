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
from src.ui.i18n import t


@dataclass
class Option:
    """Tek bir ayar: anahtar, etiket **anahtarlari**, degerler.

    Etiketler dize degil dil anahtari tutar. Bu liste modul yuklenirken bir
    kez kurulur; metni burada saklasaydik oyuncunun dil degistirmesi hicbir
    sey yapmazdi - eski dil import aninda pismis olurdu. `label` ve `note`
    birer ozellik: cizim aninda, o anki dilde cozulurler.
    """

    key: str
    label_key: str
    values: tuple[Any, ...]
    label_keys: tuple[str, ...]
    default_index: int = 0
    note_key: str = ""                  # Ayarlar ekraninda alt aciklama

    @property
    def label(self) -> str:
        return t(self.label_key)

    @property
    def note(self) -> str:
        return t(self.note_key) if self.note_key else ""

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(t(k) for k in self.label_keys)

    def index_of(self, value: Any) -> int:
        try:
            return self.values.index(value)
        except ValueError:
            return self.default_index

    def label_for(self, value: Any) -> str:
        return t(self.label_keys[self.index_of(value)])


@dataclass
class Slider:
    """Surekli deger - ses seviyeleri ve parlaklik."""

    key: str
    label_key: str
    default: float = 1.0
    step: float = 0.05
    note_key: str = ""

    @property
    def label(self) -> str:
        return t(self.label_key)

    @property
    def note(self) -> str:
        return t(self.note_key) if self.note_key else ""


# --- Sekme tanimlari --------------------------------------------------------
DISPLAY_OPTIONS: tuple[Option | Slider, ...] = (
    Option("fullscreen", "settings.fullscreen", (False, True),
           ("settings.fullscreen_windowed", "settings.fullscreen_on")),
    Option("scale", "settings.scale", (0, 2, 3, 4),
           ("settings.scale_auto", "settings.scale_2x", "settings.scale_3x",
            "settings.scale_4x")),
    Option("screen_shake", "settings.screen_shake", (0.0, 0.5, 1.0),
           ("common.off", "settings.screen_shake_low",
            "settings.screen_shake_normal"),
           default_index=2,
           note_key="settings.screen_shake_note"),
    Option("colorblind", "settings.colorblind",
           ("none", "protanopia", "deuteranopia", "tritanopia"),
           ("settings.colorblind_none", "settings.colorblind_prot",
            "settings.colorblind_deut", "settings.colorblind_trit")),
    Option("postfx", "settings.postfx", (0.0, 0.5, 1.0),
           ("common.off", "settings.postfx_low", "settings.postfx_normal"),
           default_index=2,
           note_key="settings.postfx_note"),
    Option("ui_scale", "settings.ui_scale", (1, 2),
           ("settings.ui_scale_normal", "settings.ui_scale_large")),
    Slider("brightness", "settings.brightness", default=1.0,
           note_key="settings.brightness_note"),
)

AUDIO_OPTIONS: tuple[Option | Slider, ...] = (
    Slider("volume_master", "settings.volume_master", default=0.9),
    Slider("volume_music", "settings.volume_music", default=0.6),
    Slider("volume_sfx", "settings.volume_sfx", default=0.8),
    Slider("volume_echo", "settings.volume_echo", default=0.7,
           note_key="settings.volume_echo_note"),
)

GAMEPLAY_OPTIONS: tuple[Option | Slider, ...] = (
    # Dil secenegi kendi adini hic cevirmez: "Türkçe" ve "English" her dilde
    # ayni yazilir. Yanlis dile dusen oyuncu geri donebilmeli.
    Option("language", "settings.language", ("tr", "en"),
           ("settings.lang_tr", "settings.lang_en")),
    Option("damage_taken", "settings.damage_taken", (0.5, 0.75, 1.0, 1.5),
           ("settings.pct_50", "settings.pct_75",
            "settings.pct_100", "settings.pct_150"),
           default_index=2),
    Option("enemy_speed", "settings.enemy_speed", (0.75, 1.0),
           ("settings.pct_75", "settings.pct_100"), default_index=1),
    Option("echo_penalty", "settings.echo_penalty", (True, False),
           ("common.on", "common.off"),
           note_key="settings.echo_penalty_note"),
    Option("auto_combo", "settings.auto_combo", (False, True),
           ("common.off", "common.on"),
           note_key="settings.auto_combo_note"),
    Option("damage_numbers", "settings.damage_numbers", (False, True),
           ("common.off", "common.on")),
    Option("rumble", "settings.rumble", (True, False),
           ("common.on", "common.off")),
)

TABS: tuple[tuple[str, tuple], ...] = (
    ("settings.tab_display", DISPLAY_OPTIONS),
    ("settings.tab_audio", AUDIO_OPTIONS),
    ("settings.tab_gameplay", GAMEPLAY_OPTIONS),
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
