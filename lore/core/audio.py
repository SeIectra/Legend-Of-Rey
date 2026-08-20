"""Ses motoru: bus'lar, konumsal SFX, muzik gecisi ve prosedurel ses sentezi.

Neden sentez? Sanati kodla urettigimiz gibi sesi de uretiyoruz: tek bir "ses
paleti" (kisa zarf, dusuk bit derinligi hissi, ayni gurultu karakteri) tum
efektleri birbirine baglar. Disk uzerinde dosya varsa o kullanilir; yoksa
sentez devreye girer. Boylece oyun hicbir zaman sessiz kalmaz.

Ses seviyeleri iki katmanli: her Sound nesnesi kendi *taban* seviyesini bilir,
bus carpani uzerine binder. Eski kodda seviye dogrudan Sound'a yaziliyordu,
bu yuzden ayarlar her degistiginde efektlerin goreli dengesi bozuluyordu.
"""
from __future__ import annotations

import math

import pygame

try:
    import numpy as np
except ImportError:                     # numpy yoksa sentez kapanir, oyun caliisr
    np = None

SAMPLE_RATE = 44100
CHANNELS = 2
NUM_CHANNELS = 32                       # Es zamanli SFX kapasitesi


class AudioEngine:
    def __init__(self, config, assets) -> None:
        self.config = config
        self.assets = assets
        self.enabled = False

        self.master = float(config.get("master_volume", 0.9))
        self.music_vol = float(config.get("music_volume", 0.6))
        self.sfx_vol = float(config.get("sfx_volume", 0.8))

        self._base_volumes: dict[str, float] = {}
        self._current_music: str | None = None
        self._listener = (0.0, 0.0)
        self._audible_width = 340.0     # Bu mesafeden sonra ses duyulmaz
        # Ayni sesin ayni karede onlarca kez calmasini onler (dusman surusu).
        self._recent: dict[str, int] = {}
        self._frame = 0

        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, CHANNELS, 512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(NUM_CHANNELS)
            self.enabled = True
        except pygame.error as exc:
            print(f"[audio] ses aygiti acilamadi, sessiz devam ediliyor: {exc}")
            self.enabled = False

    # --- Bus seviyeleri -----------------------------------------------------
    def apply_config(self) -> None:
        self.master = float(self.config.get("master_volume", 0.9))
        self.music_vol = float(self.config.get("music_volume", 0.6))
        self.sfx_vol = float(self.config.get("sfx_volume", 0.8))
        if self.enabled:
            pygame.mixer.music.set_volume(self.master * self.music_vol)

    def set_listener(self, x: float, y: float) -> None:
        """Konumsal ses icin dinleyici (genelde kamera merkezi)."""
        self._listener = (x, y)

    def begin_frame(self) -> None:
        self._frame += 1

    # --- SFX ----------------------------------------------------------------
    def play(self, key: str, volume: float = 1.0, pitch: float = 0.0,
             pos: tuple[float, float] | None = None, dedupe: bool = True) -> None:
        """Bir efekt calar.

        `pitch`: yari-ton cinsinden rastgelelestirme araligi degil, dogrudan
        kayma. Ayni sesin ust uste yigilmasini kirmak icin cagiran taraf
        kucuk rastgele degerler gecer.
        `pos`: verilirse mesafeye gore kisilir ve saga/sola yayilir.
        """
        if not self.enabled:
            return
        if dedupe and self._recent.get(key) == self._frame:
            return
        sound = self._resolve(key, pitch)
        if sound is None:
            return
        self._recent[key] = self._frame

        base = self._base_volumes.get(key, 1.0)
        gain = self.master * self.sfx_vol * base * volume
        left = right = gain

        if pos is not None:
            lx, ly = self._listener
            dx = pos[0] - lx
            dist = math.hypot(dx, pos[1] - ly)
            falloff = max(0.0, 1.0 - dist / self._audible_width)
            if falloff <= 0.0:
                return
            gain *= falloff * falloff
            pan = max(-1.0, min(1.0, dx / (self._audible_width * 0.5)))
            left = gain * math.sqrt(max(0.0, (1.0 - pan) * 0.5))
            right = gain * math.sqrt(max(0.0, (1.0 + pan) * 0.5))

        channel = pygame.mixer.find_channel(True)
        if channel is None:
            return
        channel.play(sound)
        try:
            channel.set_volume(min(1.0, left), min(1.0, right))
        except pygame.error:
            pass

    def _resolve(self, key: str, pitch: float) -> pygame.mixer.Sound | None:
        """Bir ses anahtarini once diskte, sonra sentezde arar."""
        cache_key = f"{key}@{pitch:.2f}" if pitch else key
        cached = self.assets._sounds.get(cache_key)
        if cached is not None:
            return cached

        spec = SFX.get(key)
        sound: pygame.mixer.Sound | None = None

        if spec and spec.get("file"):
            path = spec["file"]
            if self.assets.exists(path):
                sound = self.assets.sound(path)
        if sound is None and spec:
            sound = synth(spec, pitch)
        if sound is None:
            sound = self.assets.sound(f"assets/{key}.wav")

        self.assets.put_sound(cache_key, sound)
        if spec:
            self._base_volumes[key] = spec.get("gain", 1.0)
        return sound

    # --- Muzik --------------------------------------------------------------
    def play_music(self, path: str, loop: bool = True, fade_ms: int = 900) -> None:
        if not self.enabled or self._current_music == path:
            return
        from lore.core.paths import resource
        target = resource(path)
        if not target.is_file():
            return
        try:
            pygame.mixer.music.fadeout(fade_ms // 2)
            pygame.mixer.music.load(str(target))
            pygame.mixer.music.set_volume(self.master * self.music_vol)
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
            self._current_music = path
        except pygame.error as exc:
            print(f"[audio] muzik calinamadi ({path}): {exc}")

    def stop_music(self, fade_ms: int = 600) -> None:
        if self.enabled:
            pygame.mixer.music.fadeout(fade_ms)
        self._current_music = None

    def duck(self, amount: float = 0.35) -> None:
        """Diyalog/boss girisinde muzigi gecici olarak kisar."""
        if self.enabled:
            pygame.mixer.music.set_volume(self.master * self.music_vol * amount)

    def unduck(self) -> None:
        if self.enabled:
            pygame.mixer.music.set_volume(self.master * self.music_vol)

    def shutdown(self) -> None:
        if self.enabled:
            pygame.mixer.music.stop()
            pygame.mixer.stop()
            pygame.mixer.quit()
        self.enabled = False


# --- Prosedurel sentez ------------------------------------------------------
# Her efekt bir "recete": dalga tipi, frekans egrisi, zarf, gurultu orani.
SFX: dict[str, dict] = {
    "swing":     {"wave": "noise", "f0": 900, "f1": 240, "dur": 0.16, "decay": 5.0, "gain": 0.35, "file": "assets/attack.wav"},
    "hit_flesh": {"wave": "noise", "f0": 420, "f1": 90,  "dur": 0.20, "decay": 7.0, "gain": 0.55, "file": "assets/hit.wav"},
    "hit_armor": {"wave": "square","f0": 1400,"f1": 300, "dur": 0.14, "decay": 9.0, "gain": 0.40},
    "jump":      {"wave": "square","f0": 320, "f1": 620, "dur": 0.13, "decay": 6.0, "gain": 0.28, "file": "assets/jump.wav"},
    "land":      {"wave": "noise", "f0": 260, "f1": 70,  "dur": 0.13, "decay": 9.0, "gain": 0.30},
    "dash":      {"wave": "noise", "f0": 1600,"f1": 380, "dur": 0.22, "decay": 6.0, "gain": 0.30},
    "step":      {"wave": "noise", "f0": 320, "f1": 150, "dur": 0.07, "decay": 14.0,"gain": 0.14, "file": "assets/footstep.wav"},
    "hurt":      {"wave": "saw",   "f0": 340, "f1": 110, "dur": 0.28, "decay": 5.0, "gain": 0.50},
    "death":     {"wave": "saw",   "f0": 280, "f1": 55,  "dur": 0.60, "decay": 2.6, "gain": 0.55},
    "shoot":     {"wave": "square","f0": 780, "f1": 1500,"dur": 0.12, "decay": 8.0, "gain": 0.30, "file": "assets/shoot.wav"},
    "pickup":    {"wave": "sine",  "f0": 700, "f1": 1350,"dur": 0.16, "decay": 5.0, "gain": 0.35},
    "essence":   {"wave": "sine",  "f0": 900, "f1": 1600,"dur": 0.12, "decay": 7.0, "gain": 0.22},
    "heal":      {"wave": "sine",  "f0": 520, "f1": 1040,"dur": 0.45, "decay": 3.0, "gain": 0.40},
    "parry":     {"wave": "square","f0": 1800,"f1": 900, "dur": 0.18, "decay": 7.0, "gain": 0.50},
    "ui_move":   {"wave": "square","f0": 620, "f1": 620, "dur": 0.05, "decay": 18.0,"gain": 0.20},
    "ui_select": {"wave": "square","f0": 500, "f1": 900, "dur": 0.10, "decay": 9.0, "gain": 0.28},
    "ui_back":   {"wave": "square","f0": 500, "f1": 260, "dur": 0.10, "decay": 9.0, "gain": 0.24},
    "door":      {"wave": "noise", "f0": 180, "f1": 60,  "dur": 0.50, "decay": 3.5, "gain": 0.35},
    "checkpoint":{"wave": "sine",  "f0": 440, "f1": 880, "dur": 0.70, "decay": 2.2, "gain": 0.45},
    "break":     {"wave": "noise", "f0": 800, "f1": 120, "dur": 0.26, "decay": 7.0, "gain": 0.42},
    "boss_roar": {"wave": "saw",   "f0": 150, "f1": 60,  "dur": 1.10, "decay": 1.8, "gain": 0.65},
    # --- Yanki sesleri ------------------------------------------------------
    # Bir yanki konustugunda calar. Gecikmeli kopyalar sesin "uzaktan" ve
    # "gecmisten" geldigi hissini veriyor.
    "echo_voice": {"wave": "sine", "f0": 520, "f1": 384, "dur": 0.26, "decay": 4.2,
                   "gain": 0.30, "echo": (0.155, 4, 0.60)},
    "echo_call":  {"wave": "tri",  "f0": 288, "f1": 576, "dur": 0.42, "decay": 2.4,
                   "gain": 0.38, "echo": (0.225, 3, 0.55)},
    "echo_bond":  {"wave": "sine", "f0": 392, "f1": 784, "dur": 0.70, "decay": 1.9,
                   "gain": 0.42, "echo": (0.30, 3, 0.62)},
}


def synth(spec: dict, pitch: float = 0.0) -> pygame.mixer.Sound | None:
    """Receteye gore bir Sound uretir.

    Frekans dogrusal degil ussel suzulur - kulak frekansi logaritmik algilar,
    dogrusal suzulme "yapay" duyulur.
    """
    if np is None or not pygame.mixer.get_init():
        return None

    dur = float(spec.get("dur", 0.2))
    n = max(1, int(SAMPLE_RATE * dur))
    t = np.linspace(0.0, dur, n, endpoint=False)

    shift = 2.0 ** (pitch / 12.0)
    f0 = float(spec.get("f0", 440)) * shift
    f1 = float(spec.get("f1", f0)) * shift
    freq = f0 * (f1 / f0) ** (t / dur) if f0 > 0 and f1 > 0 else np.full(n, f0)

    wave = spec.get("wave", "sine")
    if wave == "noise":
        rng = np.random.default_rng(int(f0 * 7 + f1 * 13) & 0xFFFF)
        signal = rng.uniform(-1.0, 1.0, n)
        # Gurultuyu frekans egrisiyle renklendir: tek kutuplu alcak geciren.
        alpha = np.clip(freq / (SAMPLE_RATE * 0.5), 0.02, 0.98)
        out = np.empty(n)
        acc = 0.0
        for i in range(n):
            acc += alpha[i] * (signal[i] - acc)
            out[i] = acc
        signal = out * 2.4
    else:
        phase = np.cumsum(2.0 * np.pi * freq / SAMPLE_RATE)
        if wave == "square":
            signal = np.sign(np.sin(phase))
        elif wave == "saw":
            signal = 2.0 * ((phase / (2 * np.pi)) % 1.0) - 1.0
        elif wave == "tri":
            signal = 2.0 * np.abs(2.0 * ((phase / (2 * np.pi)) % 1.0) - 1.0) - 1.0
        else:
            signal = np.sin(phase)

    envelope = np.exp(-float(spec.get("decay", 6.0)) * t)
    attack = min(n, int(SAMPLE_RATE * 0.004))   # Klik sesini onleyen kisa atak
    if attack > 1:
        envelope[:attack] *= np.linspace(0.0, 1.0, attack)
    signal = signal * envelope * float(spec.get("gain", 0.4))

    # Yanki kuyrugu: sesin gecikmeli ve sonen kopyalari.
    # Reverb degil, ayrik yanki - "bos bir vadide seslenmek" gibi. Yanki
    # duyulur olmali, ortama karisip kaybolmamali; oyunun anlati merkezinde
    # yankilar var ve oyuncu onlari *ayirt edebilmeli*.
    tail = spec.get("echo")
    if tail:
        delay_s, repeats, feedback = tail
        delay_n = max(1, int(SAMPLE_RATE * delay_s))
        out = np.zeros(n + delay_n * repeats)
        out[:n] = signal
        amp = 1.0
        for r in range(1, repeats + 1):
            amp *= feedback
            start = delay_n * r
            # Her yinelemede biraz daha bogugu: uzaktan gelme hissi
            out[start:start + n] += signal * amp
        signal = out

    signal = np.clip(signal, -1.0, 1.0)
    pcm = (signal * 32767).astype(np.int16)
    stereo = np.repeat(pcm[:, None], CHANNELS, axis=1)
    try:
        return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))
    except (pygame.error, ValueError):
        return None
