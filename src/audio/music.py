"""Muzik yonetmeni - hangi an hangi parca.

Arda dokuz parca yukledi (30.08.2026) ve her birinin isini soyledi.
Bu modul o eslemeyi tek yerde tutuyor.

## `pygame.mixer.music`, `Sound` DEGIL

Muzik **akis** olarak calmiyor: `Sound` MP3'u tamamen belege acar ve
Fade.mp3 (479 saniye) cozuldugunde ~80 MB tutar. Dokuz parca birden
yuklenirse yarim gigabayt. `mixer.music` diskten akitiyor ve ayni anda
tek parca calmasi zaten istedigimiz sey.

Bedeli: gercek capraz gecis yok (tek akis var). Yerine `fadeout` +
`fade_ms` ile temiz bir sonup-acilma - oyun icinde fark edilmiyor cunku
gecisler zaten oda/dovus sinirlarinda oluyor.

## Baglam -> parca

Sahneler "hangi dosya" demiyor, "ne oluyor" diyor. Dosya adi tek yerde;
Arda yarin parcayi degistirirse tek satir degisiyor.

## Sessizlik korunuyor

`docs/derinlestirme.md` 6.3: *"Sessizlik, muzikten daha guclu bir
enstrumandir."* Gizli alanda muzik kesiliyor (`game.music_hush`), boss
olurken iki saniye tam sessizlik. `duck()` o kanali acik tutuyor -
`music_hush` bir donem doldurulup hic okunmuyordu, artik okunuyor.
"""
from __future__ import annotations

from pathlib import Path

import pygame

MUSIC_DIR = Path(__file__).resolve().parents[2] / "assets" / "audio" / "music"

# --- Baglam -> dosya ---------------------------------------------------------
# Arda'nin 30.08.2026 talimatiyla birebir:
#
#   Azula          ana menu
#   Fade           normal oyun ici kesif
#   Mai            dovus
#   Fuze           mini-boss (kisa olan)
#   Iron and Bone  buyuk boss (uzun olan)
#   Rey            butun Yanki kisimlari
#   Ardo           oteki karakterin girisi
#   Loki           uzucu kisimlar
#   Raze           cok nadir duygusal anlar
TRACKS: dict[str, str] = {
    "menu": "Azula.mp3",
    "explore": "Fade.mp3",
    "combat": "Mai.mp3",
    "miniboss": "Fuze.mp3",
    "boss": "Iron and Bone.mp3",
    "echo": "Rey.mp3",
    "companion": "Ardo.mp3",
    "sad": "Loki.mp3",
    "emotional": "Raze.mp3",
}

# Gecis sureleri (milisaniye). Dovuse girmek ANI olmali - tehlike
# gecikmeli gelirse oyuncu once vurulur sonra muzigi duyar. Cikis daha
# yavas: dovus bitince gerilim hemen dusmez.
FADE_IN_MS = 900
FADE_OUT_MS = 1400
COMBAT_FADE_IN_MS = 350

# Dovus muzigi son dusman uyanikligini yitirdikten sonra bu kadar kare
# daha calar. Olmasaydi tek bir dusmanin gozden kaybolmasi muzigi
# kesip acar ve "titrer".
COMBAT_LINGER_FRAMES = 150


class MusicDirector:
    """Tek akis, baglama gore parca secimi."""

    def __init__(self, settings) -> None:
        self.settings = settings
        self.context = ""
        self.hush = 0.0
        # Senaryolu anlar icin kilit: bu kare sayisi boyunca baglam
        # degistirilemiyor. Olmasaydi dovus durum makinesi (`_update_music`)
        # bir sonraki karede kurtarma/duygusal parcayi ezerdi - ve tam
        # olarak oyle oluyordu.
        self.locked_frames = 0
        self.available = MUSIC_DIR.is_dir()
        self._failed: set[str] = set()

    # --- Denetim ------------------------------------------------------------
    def play(self, context: str, *, fade_ms: int | None = None) -> None:
        """Baglami degistirir. Ayni baglamsa **hicbir sey yapmaz**.

        Tekrar `play` cagirmak parcayi bastan baslatirdi; sahneler bunu
        her karede cagirdigi icin sarti burada tutmak sart.
        """
        if context == self.context or self.locked_frames > 0:
            return
        name = TRACKS.get(context)
        if name is None or name in self._failed:
            return
        path = MUSIC_DIR / name
        if not path.is_file():
            self._failed.add(name)
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self._volume())
            pygame.mixer.music.play(
                loops=-1,
                fade_ms=FADE_IN_MS if fade_ms is None else fade_ms)
        except pygame.error:
            # Bir parca acilamazsa oyun **durmaz**: sessiz devam eder ve
            # bir daha denenmez. Muzik bir sus payi, bir zorunluluk degil.
            self._failed.add(name)
            return
        self.context = context

    def hold(self, context: str, frames: int, *,
             fade_ms: int | None = None) -> None:
        """Bir parcayi calip `frames` kare boyunca **kilitler**.

        Senaryolu anlar icin: kurtarma, duygusal beat, uzucu sahne.
        Kilit olmadan `PlayScene._update_music` bir sonraki karede
        dovus/kesif baglamina donuyor ve an sessizce kayboluyor.
        """
        self.locked_frames = 0          # once kilidi ac ki `play` gecsin
        self.play(context, fade_ms=fade_ms)
        self.locked_frames = max(0, frames)

    def stop(self, fade_ms: int = FADE_OUT_MS) -> None:
        if not self.context:
            return
        try:
            pygame.mixer.music.fadeout(fade_ms)
        except pygame.error:
            pass
        self.context = ""

    def duck(self, amount: float) -> None:
        """0 = normal, 1 = tamamen sessiz. `game.music_hush` buraya baglı."""
        self.hush = max(0.0, min(1.0, amount))

    def update(self) -> None:
        """Her kare hacmi tazeler - ayar ve `hush` degisebilir."""
        if self.locked_frames > 0:
            self.locked_frames -= 1
        if not self.context:
            return
        try:
            pygame.mixer.music.set_volume(self._volume())
        except pygame.error:
            pass

    def _volume(self) -> float:
        master = float(self.settings.get("volume_master", 0.9))
        music = float(self.settings.get("volume_music", 0.6))
        return max(0.0, master * music * (1.0 - self.hush))


def combat_context(scene) -> str:
    """Sahnenin durumundan dovus baglamini turetir.

    Sira **onemli**: buyuk boss > mini-boss > dovus > kesif. Bir boss
    odasindaki siradan dusmanlar dovus muzigini calmasin - o odanin
    muzigi boss'un.
    """
    boss = getattr(scene, "boss", None)
    if boss is not None and not getattr(boss, "dead", True):
        # `Boss` alt siniflarindan hangisi? Buyuk boss'un faz esikleri
        # birden fazla; mini-boss'un tek. Sinif adi yerine **davranisa**
        # bakiyoruz - yeni bir boss eklendiginde liste guncellenmek
        # zorunda kalmasin.
        phases = getattr(boss, "phases", ())
        return "boss" if len(phases) >= 2 else "miniboss"
    return ""
