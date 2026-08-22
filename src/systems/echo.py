"""Yanki - oyunun ana mekanigi.

`docs/gdd.md` 4 baglayici. Rey'in laneti: kafasindaki sesler ona yol
gosterir. Tutorial, ipucu ve bilgi bu sesle gelir - diegetik arayuz.

## Uc kademe

    BERRAK   duvar ardindaki dusman siluetleri, gizli gecitler parlar
    BULANIK  yalnizca yakin mesafe, uyari var detay yok
    SESSIZ   hicbir yardim yok (Ardo'nun standart oynanisi)

Olunce **bir kademe duser**. Dip SESSIZ - daha asagi inmez, olum sarmali
engellenir. Yirmi combo bir kademe iyilestirir; kontrol noktalari da.

## Bedel

Aktifken ekran kenari kararir, sesler boguklasir, **savunma duser**.
Yardim bedava degil: bilgi aliyorsun, dayanikliligindan veriyorsun.

Gorevin bitis olcutu tek cumle: *"Yanki'yi actigimda hem yardim aldigimi
hem bir sey kaybettigimi AYNI ANDA hissetmeliyim."* Bu yuzden acma ve
kapama **aninda** degil: acilirken kisa bir yukselme, kapanirken sonme var.
Aninda gecis bir dugme gibi okunur; kademeli gecis bir **hal** gibi.

## Yanki yalan soyleyebilir

`ask()` icindeki en onemli satir bu. Kademe dustukce yalan olasiligi
artiyor ve oyuncu kademesini **bildigi** icin riski kendi hesapliyor
(docs/derinlestirme.md 2.1). Ana mekanik boylece pasif bir guclendirmeden
bir **iliskiye** doniyor: ona guveniyor musun?

B14'teki donusun tohumu burada: Yanki hep yardim ediyordu cunku Rey'i
cagiriyordu.
"""
from __future__ import annotations

import random
from enum import IntEnum

from src.config import (
    ECHO_DAMAGE_TAKEN_MULTIPLIER, ECHO_TIER_CLEAR, ECHO_TIER_MURKY,
    ECHO_TIER_SILENT, ECHO_VIGNETTE_STRENGTH, SONAR_COOLDOWN_FRAMES,
    SONAR_PULSE_FRAMES,
)

# Acilma/kapanma egrisi - kare cinsinden.
RISE_FRAMES = 14
FALL_FRAMES = 20

# Kademeye gore gorus menzili (piksel). SESSIZ hicbir sey gostermez.
SIGHT_RANGE = {
    ECHO_TIER_CLEAR: 260.0,
    ECHO_TIER_MURKY: 96.0,
    ECHO_TIER_SILENT: 0.0,
}

# Kademeye gore yalan olasiligi. BERRAK asla yalan soylemez - guven once
# kurulur, sonra sarsilir.
LIE_CHANCE = {
    ECHO_TIER_CLEAR: 0.0,
    ECHO_TIER_MURKY: 0.35,
    ECHO_TIER_SILENT: 1.0,
}

COMBO_TO_RESTORE = 20        # Saldirgan oynayan kademesini geri kazanir


class Answer(IntEnum):
    """Yanki'ya sorulan sorunun cevabi."""

    NONE = 0        # Sessiz - cevap yok
    TRUTH = 1       # Dogru yon
    PARTIAL = 2     # Eksik: yon var, mesafe yok
    LIE = 3         # Yanlis yon - ve bunu soylemiyor


class EchoState:
    """Bir oyuncunun Yanki durumu.

    Ardo'da hic olusturulmaz; `has_echo` False olan karakterlerde sistem
    devre disi kalir ve kod her yerde `if echo is None` diye dallanmaz.
    """

    def __init__(self, tier: int = ECHO_TIER_CLEAR,
                 seed: int | None = None) -> None:
        self.tier = tier
        self.holding = False
        self.strength = 0.0          # 0..1 - acilma/kapanma egrisi
        self.ask_cooldown = 0
        self.last_answer = Answer.NONE
        self.answer_frames = 0
        # Yalan **karar** anindan bagimsiz olmali: ayni soru ayni karede
        # iki kez sorulursa ayni cevabi vermeli. Sahne basina sabit tohum.
        self._rng = random.Random(seed)

        # Ses haritasi (sonar) - Bolum 3 Oda 2. `ask()`in ayni cooldown
        # deseni ama surekli acilma/kapanma egrisi degil: tek seferlik
        # genisleyen bir halka. `holding`dan bagimsiz - karanlik bir odada
        # Yanki'yi **aktive etmek** bu darbeyi tetikliyor.
        self.sonar_cooldown = 0
        self.sonar_frames = 0
        self._sonar_total = 0

    # --- Sorgular -----------------------------------------------------------
    @property
    def silent(self) -> bool:
        return self.tier <= ECHO_TIER_SILENT

    @property
    def active(self) -> bool:
        """Gorsel olarak acik mi - egri sifirdan buyukse evet."""
        return self.strength > 0.01

    @property
    def sight_range(self) -> float:
        """Su anki gorus menzili. Egri ile olceklenir."""
        return SIGHT_RANGE.get(self.tier, 0.0) * self.strength

    @property
    def vignette(self) -> float:
        """Ekran kenari kararmasi 0..1."""
        return ECHO_VIGNETTE_STRENGTH * self.strength

    @property
    def damage_multiplier(self) -> float:
        """Aktifken savunma duser - bedelin en somut parcasi."""
        return 1.0 + (ECHO_DAMAGE_TAKEN_MULTIPLIER - 1.0) * self.strength

    def tier_name(self) -> str:
        return {
            ECHO_TIER_CLEAR: "clear",
            ECHO_TIER_MURKY: "murky",
            ECHO_TIER_SILENT: "silent",
        }.get(self.tier, "silent")

    # --- Kademe -------------------------------------------------------------
    def weaken(self) -> bool:
        """Olunce bir kademe duser. Dip SESSIZ - daha asagi inmez."""
        if self.tier <= ECHO_TIER_SILENT:
            return False
        self.tier -= 1
        return True

    def restore(self) -> bool:
        """Kontrol noktasi ya da 20 combo. BERRAK tavan."""
        if self.tier >= ECHO_TIER_CLEAR:
            return False
        self.tier += 1
        return True

    # --- Dongu --------------------------------------------------------------
    def update(self, holding: bool) -> None:
        """`holding` tus basili mi. Egri burada yurur."""
        self.holding = holding and not self.silent
        # Acilirken hizli, kapanirken yavas: birakinca hemen kesilse
        # "dugme" gibi olurdu, sonerek gitmesi "hal" gibi okunuyor.
        step = 1.0 / RISE_FRAMES if self.holding else -1.0 / FALL_FRAMES
        self.strength = max(0.0, min(1.0, self.strength + step))

        if self.ask_cooldown > 0:
            self.ask_cooldown -= 1
        if self.answer_frames > 0:
            self.answer_frames -= 1
            if self.answer_frames == 0:
                self.last_answer = Answer.NONE

        if self.sonar_cooldown > 0:
            self.sonar_cooldown -= 1
        if self.sonar_frames > 0:
            self.sonar_frames -= 1

    # --- Soru sorma ---------------------------------------------------------
    def ask(self, cooldown: int = 90, display: int = 150) -> Answer:
        """Yanki'ya soru sorar. Cevabin **dogru olacagi garanti degil.**

        Kademe dustukce yalan olasiligi artar. Oyuncu kademesini bildigi
        icin riski kendi hesaplar - mekanik burada bir iliskiye doniyor.
        """
        if self.ask_cooldown > 0:
            return Answer.NONE
        self.ask_cooldown = cooldown
        self.answer_frames = display

        if self.silent:
            self.last_answer = Answer.NONE
        elif self._rng.random() < LIE_CHANCE.get(self.tier, 1.0):
            self.last_answer = Answer.LIE
        elif self.tier == ECHO_TIER_CLEAR:
            self.last_answer = Answer.TRUTH
        else:
            self.last_answer = Answer.PARTIAL
        return self.last_answer

    # --- Ses haritasi (sonar) -------------------------------------------------
    def pulse(self, cooldown: int = SONAR_COOLDOWN_FRAMES,
              duration: int = SONAR_PULSE_FRAMES) -> bool:
        """Tek seferlik genisleyen ses dalgasi baslatir.

        `ask()` ile ayni fikir (cooldown + gosterim suresi) ama tamamen
        ayri bir gorsel: surekli acilma/kapanma egrisi degil, bir kere
        genisleyip sonen bir halka (docs/bolum-03.md Oda 2). Cooldown
        bitmemisse `False` doner - oyuncu ardarda spam edemez.
        """
        if self.sonar_cooldown > 0:
            return False
        self.sonar_cooldown = cooldown
        self.sonar_frames = duration
        self._sonar_total = duration
        return True

    @property
    def sonar_active(self) -> bool:
        return self.sonar_frames > 0

    @property
    def sonar_progress(self) -> float:
        """0..1 - halka ne kadar genisledi. 0 = yeni dogdu, 1 = sonuyor."""
        if self._sonar_total <= 0 or self.sonar_frames <= 0:
            return 0.0
        return 1.0 - (self.sonar_frames / self._sonar_total)
