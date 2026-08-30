"""Sinematik sahneleme - ara sahnelere **oyuncu** koyan katman.

## Neden gerekti

`story.py` bir ara sahneyi panel dizisine cevirdi ve letterbox/replik/
kamera islerini cozdu. Ama panelin **govdesi** hala elle yaziliyordu ve
elde yalnizca sunlar vardi: bir renkle doldur, bir hale bindir, ekrani
kaydir.

Sonuc: bugune kadarki butun ara sahnelerde **tek bir karakter cizilmedi.**
Bolum 3'un "Mor" sahnesi buyuyen bir daire; "Inis" kucululen bir daire.
Oysa oyunda 20 karakterin 12 animasyon durumu **zaten uretilmis** ve
`Animator.render()` yon/flas/deformasyon/siluet/tint/alfa'yi zaten
destekliyor. Sinematikler o zenginlige hic dokunmuyordu.

Arda (30.08.2026): *"Daha fazla sinematik ara sahne koyalim. Animasyonlu
ve efektli sahneler."* Bu modul o istegin altyapisi.

## Sahneleme dili

Panel **ne oldugunu** soyluyordu; `Cue` **kimin ne yaptigini** soyluyor:

    Panel(90, "el", cues=(
        Cue("ardo", state="idle", face=-1),
        Cue("rey", move_to=(120, 150), move_frames=60, state="run"),
        Cue("rey", delay=60, state="idle", sound="land_hard"),
    ))

Neden veri, neden `if frame > 90:` degil: Bolum 3'un iki sinematigi elle
kare esigi karsilastiriyordu ve **birbirinden farkli davraniyorlardi** -
biri letterbox'i unutmustu, oteki hizlandirmayi. Ayni ders `story.py`'nin
en ustunde de yazili. Talimat veri olunca sahne onu tek yerden, tek
bicimde uyguluyor.

## Kare, saniye degil

Her sure kare (CLAUDE.md 4). `move_frames=60` bir saniye demek ve
hizlandirma (basili tutma) bunu **bozmaz**: `StoryScene` ilerlemeyi
hizlandirir, aktorun kendi ic sayaci ayni ilerlemeden beslenir.

## Cizim sirasi

    arka plan -> ISIK (eklemeli) -> aktorler (y'ye gore) -> parcacik
    -> on plan -> vinyet -> flas -> letterbox -> replik

Isik aktorlerden ONCE: hale bir atmosfer, bir onluk degil. Aktorun
uzerine binerse karakter sisin arkasinda kalir ve siluet okunmaz -
`CLAUDE.md` 6'nin siluet testi tam olarak bunu yasakliyor. Karakterin
isikla iliskisi `rim_light` ile kuruluyor: siluetin isik tarafindaki tek
piksellik serit.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from src.art import palette
from src.art.animator import Animator
from src.art.glow import radial_glow, rim_light
from src.art.particles import ParticleField
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.cinematic import smoothstep
from src.scenes.story import Panel, StoryScene

def ease_in(t_value: float) -> float:
    """Hizlanan hareket. **Dusus icin.**

    `smoothstep` hem hizlanip hem yavasliyor; bir dusus icin yanlis -
    karakter yere yaklasirken yavasliyor ve carpma gucunu kaybediyor.
    Yer cekimi yavaslamaz.
    """
    t_value = max(0.0, min(1.0, t_value))
    return t_value * t_value


def ease_out(t_value: float) -> float:
    """Yavaslayan hareket - bir yere varmak, durmak."""
    t_value = max(0.0, min(1.0, t_value))
    return 1.0 - (1.0 - t_value) ** 2


def ease_linear(t_value: float) -> float:
    return max(0.0, min(1.0, t_value))


EASINGS = {
    "in": ease_in,
    "out": ease_out,
    "inout": smoothstep,
    "linear": ease_linear,
}

# Zemin golgesi (CLAUDE.md 6: "karakterin altinda 1 elips").
SHADOW_WIDTH = 18
SHADOW_HEIGHT = 5

# Ekran flasi bu kadar karede soner. 8 = ~130ms: bir vurus kadar kisa.
# Uzun olsaydi "flas" degil "beyaz ekran" olurdu.
FLASH_DECAY_FRAMES = 8

# Vinyet karartmasinin en koyu hali (0..255).
VIGNETTE_MAX = 200

# Yakin plan: portre bu kadar buyutuluyor (**tam sayi**, CLAUDE.md 4).
CLOSEUP_SCALE = 3
# Portrenin ust kismindan kirpilan piksel - yuz kadrajin ust yarisina
# gelsin diye. Portrede kafa 40 piksel, govde altta ve gereksiz.
CLOSEUP_HEAD_OFFSET = 9
# Yakin plandaki kenar karartmasinin yaricapi ve siddeti.
CLOSEUP_VIGNETTE = 165
# Karartma **hafif**: 120 denendi ve yuzu yedi - portrenin kendi
# renkleri zaten koyu, uzerine agir bir vinyet binince yalnizca
# gozler seciliyordu. Amac dikkati toplamak, sahneyi karartmak
# degil.
CLOSEUP_DIM = 48

# Atmosfer zerresi ust siniri. `ParticleField`den ayri: bunlar olay
# degil **ortam** - dogmuyor, olmuyor, sadece suruklenip ekranin obur
# ucundan geri giriyorlar. Parcacik butcesini (200) yemiyorlar.
MOTE_LIMIT = 48


class MoteField:
    """Suruklenen toz/kul zerreleri - sahnenin havasi.

    Neden `ParticleField` degil: parcaciklar bir OLAYIN sonucu (vurus,
    kirilma) ve oluyorlar. Bunlar bir MEKANIN ozelligi - magaranin
    havasinda asili duran seyler. Omurleri yok, ekrandan cikinca obur
    uctan giriyorlar.

    Dagilim **deterministik**: `random` yok, indeksten turuyor. Ayni
    sahne her acilista ayni gorunuyor - `cave_backdrop`'un ve
    `chapter02_cinematics`'in zaten kullandigi desen. Bir ara sahnenin
    her oynanista farkli gorunmesi bir ozellik degil, bir kaza olurdu.
    """

    __slots__ = ("count", "drift", "sway", "tone", "cells", "frame")

    def __init__(self, count: int = 30, drift: float = -0.35,
                 sway: float = 0.6, tone: str = "stone_dark") -> None:
        self.count = min(count, MOTE_LIMIT)
        self.drift = drift          # dikey hiz (- yukari)
        self.sway = sway            # yatay salinim genligi
        self.tone = tone
        self.frame = 0
        self.cells = tuple(
            (
                (index * 137 + 41) % INTERNAL_WIDTH,
                (index * 89 + 17) % INTERNAL_HEIGHT,
                0.55 + (index % 5) * 0.22,      # hiz carpani
                1 + (index % 4) // 3,           # boyut (cogu 1 piksel)
                index * 0.7,                    # salinim fazi
            )
            for index in range(self.count)
        )

    def update(self) -> None:
        self.frame += 1

    def draw(self, surface: pygame.Surface, alpha: float = 1.0) -> None:
        if alpha <= 0.02:
            return
        colour = tuple(int(c * min(1.0, alpha))
                       for c in palette.color(self.tone))
        for x, y, speed, size, phase in self.cells:
            offset = self.frame * self.drift * speed
            py = int(y + offset) % (INTERNAL_HEIGHT + 8) - 4
            px = int(x + math.sin(self.frame * 0.02 + phase) * self.sway * 4)
            px %= INTERNAL_WIDTH
            surface.fill(colour, (px, py, size, size))


@dataclass
class ActorSpec:
    """Sahneye kimin, nerede, nasil girdigi."""

    name: str                       # sahne icindeki takma ad ("rey", "golge")
    character: str                  # `animation.CHARACTERS` anahtari
    x: float
    y: float                        # **ayak** hizasi
    facing: int = 1
    state: str = "idle"
    alpha: int = 255
    # Siluet kipi: karakter tek renk. "Golge yukaridan duser" gibi
    # kimligin henuz belli olmadigi anlar icin (docs/yapi.md B6).
    silhouette: bool = False
    visible: bool = True
    # Zemin golgesi. **Havadaki aktorde kapatilmali**: dusen bir
    # karaktere temas golgesi cizmek onu havada degil bir yuzeyin
    # uzerinde gosterir. Bolum 2'nin dusus sahnesinde tam olarak oyle
    # gorunuyordu - Rey dusuyor ama altinda bir golge duruyordu.
    shadow: bool = True
    # **Derinlik.** Kamera kaydiginda aktor bu oranda kaiyor:
    #   1.0  on plan - kamerayla birebir
    #   0.5  orta    - yarim hizda, daha uzakta gorunuyor
    #   0.0  sonsuz  - hic kaymiyor (gokyuzu, uzaktaki dag)
    #
    # Parallaks derinligi **hareketten** dogar; tek karede goze
    # gorunmez, kamera kayinca ortaya cikar. Bu yuzden sabit bir
    # sahnede degeri yok ve varsayilani 1.0.
    depth: float = 1.0
    # Sinematik buyutmesi - **tam sayi**, `smoothscale` YASAK
    # (CLAUDE.md 4/12: piksel art bulaniklasir).
    #
    # Oynanista karakter 32 piksel ve dogru; 480x270'lik bir karede
    # duygusal bir an icin kucuk kaliyor. "El" sahnesinde iki figur
    # ekranin yuzde onunu kapliyordu ve bir saniye fazla tutulan el
    # gorunmuyordu bile. Yakin plan sahneler 2 kullaniyor, genis
    # planlar 1'de kaliyor - kamera dili, sabit bir deger degil.
    scale: int = 1


@dataclass
class Cue:
    """Bir panelde bir aktore verilen talimat.

    `delay` panelin basindan itibaren kac kare sonra islenecegini soyler;
    boylece tek panel icinde sirali bir koreografi kurulabiliyor.
    """

    actor: str
    state: str | None = None
    face: int | None = None
    move_to: tuple[float, float] | None = None
    move_frames: int = 0            # 0 = isinla
    # Hareketin egrisi: "in" hizlanan (dusus), "out" yavaslayan (varis),
    # "inout" ikisi de (varsayilan), "linear" duz.
    move_ease: str = "inout"
    delay: int = 0
    alpha: int | None = None
    silhouette: bool | None = None
    visible: bool | None = None
    # Efektler - aktorun konumunda tetiklenir.
    burst: str = ""                 # parcacik yolu ("dust", "spark", "echo")
    burst_count: int = 12
    flash: float = 0.0              # 0..1 ekran flasi
    shake: float = 0.0              # ek sarsinti
    # **Hitstop.** Sahne bu kadar kare tamamen donuyor: aktorler,
    # parcaciklar, panel sayaci - hepsi. `CLAUDE.md` 7 dovuste zaten
    # bunu zorunlu tutuyor (normal 3, bitirici 7, olduruccu 12 kare);
    # sinematikte de ayni is: bir carpmanin AGIRLIGI durustan okunuyor.
    freeze: int = 0
    sound: str = ""


class StageActor:
    """Sinematikteki bir karakter. `Animator`'i sahne icin sarar."""

    def __init__(self, spec: ActorSpec) -> None:
        self.name = spec.name
        self.animator = Animator(spec.character)
        self.animator.play(spec.state)
        self.x = float(spec.x)
        self.y = float(spec.y)
        self.facing = spec.facing
        self.alpha = spec.alpha
        self.silhouette = spec.silhouette
        self.visible = spec.visible
        self.shadow = spec.shadow
        self.depth = spec.depth
        self.scale = max(1, spec.scale)
        # Hareket: baslangic, hedef, sure, gecen kare.
        self._from: tuple[float, float] = (self.x, self.y)
        self._to: tuple[float, float] = (self.x, self.y)
        self._move_frames = 0
        self._moved = 0
        self._ease = smoothstep

    # --- Talimatlar ---------------------------------------------------------
    def ground(self, y: float) -> None:
        """Aktoru zemine koyar ve golgesini geri acar."""
        self.y = float(y)
        self.shadow = True

    def move_to(self, x: float, y: float, frames: int,
                ease: str = "inout") -> None:
        if frames <= 0:
            self.x, self.y = float(x), float(y)
            self._move_frames = 0
            return
        self._from = (self.x, self.y)
        self._to = (float(x), float(y))
        self._move_frames = frames
        self._moved = 0
        self._ease = EASINGS.get(ease, smoothstep)

    @property
    def moving(self) -> bool:
        return self._moved < self._move_frames

    def update(self) -> None:
        self.animator.update()
        if not self.moving:
            return
        self._moved += 1
        ratio = self._ease(self._moved / max(1, self._move_frames))
        self.x = self._from[0] + (self._to[0] - self._from[0]) * ratio
        self.y = self._from[1] + (self._to[1] - self._from[1]) * ratio

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int],
             light: tuple[int, int, palette.RGB] | None = None) -> None:
        if not self.visible or self.alpha <= 0:
            return
        image = self.animator.render(self.facing,
                                     silhouette_mode=self.silhouette,
                                     alpha=self.alpha)
        if image is None:
            return
        if self.scale > 1:
            image = pygame.transform.scale(
                image, (image.get_width() * self.scale,
                        image.get_height() * self.scale))
        # Derinlik: kamera ofseti bu aktore ne kadar isliyor.
        ox = int(round(offset[0] * self.depth))
        oy = int(round(offset[1] * self.depth))
        # Konum **tam sayiya yuvarlanir** - ondalik ofset piksel art
        # dokusunu titretir (CLAUDE.md 9).
        x = int(round(self.x)) - ox - image.get_width() // 2
        y = int(round(self.y)) - oy - image.get_height()

        if self.shadow:
            self._draw_shadow(surface, ox, oy)
        surface.blit(image, (x, y))
        if light is not None:
            self._draw_rim(surface, image, x, y, light)

    def _draw_shadow(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        rect = pygame.Rect(0, 0, SHADOW_WIDTH * self.scale,
                           SHADOW_HEIGHT * self.scale)
        rect.center = (int(round(self.x)) - ox,
                       int(round(self.y)) - oy)
        shadow = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (*palette.role("shadow"), 110),
                            shadow.get_rect())
        surface.blit(shadow.convert_alpha(), rect.topleft)

    def _draw_rim(self, surface: pygame.Surface, image: pygame.Surface,
                  x: int, y: int,
                  light: tuple[int, int, palette.RGB]) -> None:
        """Isigin tarafindaki kenar cizgisi.

        Hale karakterin **arkasinda** kaliyor (cizim sirasi), yani isikla
        iliskiyi kuran tek sey bu serit. Olmadan karakter aydinlatilmis
        bir odada duran duz bir sticker gibi okunuyor.
        """
        lx, _ly, colour = light
        direction = 1 if lx > self.x else -1
        # Siddet dusuk: 0.75 (varsayilan) omuzlarda beyaz bloklar
        # birakiyordu ve siluetten cok bir hata gibi okunuyordu.
        rim = rim_light(image, colour, direction, strength=0.42)
        if rim is not None:
            surface.blit(rim, (x, y))


class StagedScene(StoryScene):
    """Aktorlu, parcacikli, isikli ara sahne.

    Alt sinif `ACTORS` ve `PANELS` verir; panel govdesi icin
    `draw_stage_background` / `draw_stage_foreground` yazar. Aktorleri,
    parcaciklari, isigi ve efektleri bu sinif cizer.
    """

    ACTORS: tuple[ActorSpec, ...] = ()
    # Atmosfer zerreleri - `None` = yok. Alt sinif `MoteField` verir.
    motes: MoteField | None = None
    # Sahne kamerasi **acik**: `Panel.camera` verilirse kayiyor,
    # verilmezse ofset (0,0) kaliyor ve hicbir sey degismiyor.
    #
    # `story.py` kamerayi bastan yazmisti ama `use_camera` False'ti ve
    # hicbir sahne acmamisti - yani kaydirma kodu vardi, hic
    # calismamisti. `DEVIR.md`'nin kendi dersi: *"yazilip hic
    # calistirilmayan kod hatasiz gorunur, hatasiz degildir."*
    use_camera: bool = True
    vignette: float = 0.0           # 0 = yok, 1 = en koyu

    # --- Kurulum ------------------------------------------------------------
    def on_enter(self, **kwargs: object) -> None:
        # **Sahne once kurulur, sonra super().** `StoryScene.on_enter`
        # sonunda `_start_panel()` cagiriyor, o da `on_panel_start` ->
        # cue'lar -> `self.actors`. Sira ters olsaydi ilk panel henuz var
        # olmayan bir sozluge yazardi ve sahne acilir acilmaz patlardi -
        # nitekim ilk surumde tam olarak oyle oldu.
        self.actors: dict[str, StageActor] = {}
        self.actor_order: list[str] = []
        for spec in self.ACTORS:
            self.actors[spec.name] = StageActor(spec)
            self.actor_order.append(spec.name)
        self.particles = ParticleField()
        self.lights: list[tuple[int, int, int, palette.RGB, float]] = []
        self.flash_strength = 0.0
        self.extra_shake = 0.0
        self.freeze_frames = 0
        # Dikey/yatay kaydirma - dusus ve tirmanis sahneleri icin.
        # Aktorler bunu **yasamiyor**: kaydirilan sey arka plan, yani
        # hareket eden dunya. Ayni kural `cave_backdrop`'ta da var.
        self.scroll = 0.0
        self.scroll_speed = 0.0
        self._pending: list[tuple[int, Cue]] = []
        super().on_enter(**kwargs)

    def actor(self, name: str) -> StageActor | None:
        return self.actors.get(name)

    # --- Efekt kancalari (alt sinif da cagirabilir) -------------------------
    def flash(self, strength: float) -> None:
        self.flash_strength = max(self.flash_strength, min(1.0, strength))

    def add_light(self, x: int, y: int, radius: int,
                  colour: palette.RGB, peak: float = 0.5) -> None:
        """Kalici isik kaynagi. Panel degisiminde temizlenmez - sahnenin
        atmosferi panel sinirinda sifirlanmamali."""
        self.lights.append((x, y, radius, colour, peak))

    def clear_lights(self) -> None:
        self.lights.clear()

    def burst(self, x: float, y: float, path: str, count: int = 12,
              **kwargs) -> None:
        self.particles.burst(x, y, count, path=path, **kwargs)

    # --- Panel akisi --------------------------------------------------------
    def on_panel_start(self, panel: Panel) -> None:
        """Panelin cue'larini kuyruga alir; gecikmesizler hemen islenir."""
        self._pending = [(cue.delay, cue) for cue in getattr(panel, "cues", ())]
        self._run_due()
        self.on_stage_panel(panel)

    def _run_due(self) -> None:
        due = [cue for delay, cue in self._pending if delay <= 0]
        self._pending = [(delay - 1, cue) for delay, cue in self._pending
                         if delay > 0]
        for cue in due:
            self._apply(cue)

    def _apply(self, cue: Cue) -> None:
        actor = self.actors.get(cue.actor)
        if actor is not None:
            self._apply_to_actor(actor, cue)
        if cue.flash > 0.0:
            self.flash(cue.flash)
        if cue.shake > 0.0:
            self.extra_shake = max(self.extra_shake, cue.shake)
        if cue.freeze > 0:
            self.freeze_frames = max(self.freeze_frames, cue.freeze)
        if cue.sound:
            self.game.play_sound(cue.sound)

    def _apply_to_actor(self, actor: StageActor, cue: Cue) -> None:
        if cue.face is not None:
            actor.facing = cue.face
        if cue.state is not None:
            actor.animator.play(cue.state, restart=True)
        if cue.alpha is not None:
            actor.alpha = cue.alpha
        if cue.silhouette is not None:
            actor.silhouette = cue.silhouette
        if cue.visible is not None:
            actor.visible = cue.visible
        if cue.move_to is not None:
            actor.move_to(cue.move_to[0], cue.move_to[1], cue.move_frames,
                          cue.move_ease)
        if cue.burst:
            self.burst(actor.x, actor.y - 8, cue.burst, cue.burst_count)

    # --- Dongu --------------------------------------------------------------
    def update_cinematic(self) -> None:
        # **Hitstop: her sey durur.** Aktor, parcacik, panel sayaci.
        # Yalnizca sarsinti ve flas sonmeye devam ediyor - donmus bir
        # karede titreyen ekran, carpmanin gucunu tasiyan sey.
        if self.freeze_frames > 0:
            self.freeze_frames -= 1
            self.flash_strength = max(0.0, self.flash_strength
                                      - 1.0 / FLASH_DECAY_FRAMES)
            self.shake_seed += 1.0
            return
        super().update_cinematic()
        self._run_due()
        self.scroll += self.scroll_speed
        if self.motes is not None:
            self.motes.update()
        for actor in self.actors.values():
            actor.update()
        self.particles.update()
        self.flash_strength = max(0.0, self.flash_strength
                                  - 1.0 / FLASH_DECAY_FRAMES)
        self.extra_shake *= 0.85

    # --- Cizim --------------------------------------------------------------
    @property
    def stage_offset(self) -> tuple[int, int]:
        return self.camera.offset if self.use_camera else (0, 0)

    def draw_panel(self, surface: pygame.Surface, panel: Panel,
                   progress: float) -> None:
        # **Yakin plan panelin yerine gecer**, uzerine binmez: bir
        # yakin plan bir KESME'dir. Arkada sahne durup one bir yuz
        # konsaydi iki goruntu ayni anda yarisirdi.
        if getattr(panel, "closeup", ""):
            self._draw_closeup(surface, panel)
            self._draw_flash(surface)
            self._draw_fade(surface, panel)
            return

        offset = self.stage_offset
        # Elle cizilmis panel varsa **prosedurel arka planin yerine**
        # geciyor. Gerekce portrelerdekiyle ayni: kod uretimi taban,
        # cizim ust. Dosya yoksa hicbir sey degismiyor, yani panelleri
        # tek tek eklemek mumkun - hepsini birden bitirmek gerekmiyor.
        if not self._blit_panel_art(surface, panel):
            self.draw_stage_background(surface, panel, progress, offset)
        if self.motes is not None:
            self.motes.draw(surface)
        self._draw_lights(surface, offset)
        self._draw_actors(surface, offset)
        self.particles.draw(surface, offset)
        self.draw_stage_foreground(surface, panel, progress, offset)
        if self.vignette > 0.0:
            self._draw_vignette(surface)
        self._draw_flash(surface)
        self._draw_extra_shake(surface)
        self._draw_fade(surface, panel)

    # --- Yakin plan ---------------------------------------------------------
    def _draw_closeup(self, surface: pygame.Surface, panel: Panel) -> None:
        """Ekrani aktorun **portresi** kapliyor.

        Oyunun en iyi yuz sanati (`src/art/portrait.py`, kafa 40
        piksel) diyalog kutusunun kosesinde 1x cizilen kucuk bir
        resimdi ve baska hicbir yerde kullanilmiyordu. Duygusal bir
        beat'te yuze kesmek sinemanin en temel cumlesi.

        **Buyutme tam sayi** (`CLAUDE.md` 4/12): 3x. Ara degerler
        piksel arti bozar; 3x'te 64x96'lik portre 192x288 oluyor,
        yani kadraji dolduruyor ve kafa ekranin yarisini kapliyor.
        """
        from src.art import portrait as portrait_art
        actor = self.actors.get(panel.closeup)
        name = actor.animator.character if actor is not None else panel.closeup
        # `rey_armed`/`ardo_axe` gibi varyantlarin portresi yok - taban
        # ada dusuluyor. Olmasaydi yakin plan bos ekran olurdu.
        image = portrait_art.portrait(name) or portrait_art.portrait(
            name.split("_")[0])
        surface.fill(palette.color("ink"))
        if image is None:
            return
        scale = CLOSEUP_SCALE
        big = pygame.transform.scale(
            image, (image.get_width() * scale, image.get_height() * scale))
        x = INTERNAL_WIDTH // 2 - big.get_width() // 2
        # Yuz kadrajin **ust yarisinda**: portrenin alt kismi govde ve
        # onu gostermenin bir anlami yok. Bas hizasi ucte bire geliyor.
        y = -CLOSEUP_HEAD_OFFSET * scale
        surface.blit(big, (x, y))
        # Kenarlarda karanlik: dikkat yuze toplaniyor.
        #
        # Perde **gri doldurulup** ortasi haleyle siliniyor. Ilk surumde
        # siyah doldurulup haleyle silinmisti - siyahtan cikarmak yine
        # siyah veriyor, yani vinyet hicbir sey yapmiyordu. `glow.py`'nin
        # basligindaki kuralin dorduncu tekrari: eklemeli/cikarmali
        # harmanlamada siddet **renkle** ayarlanir.
        level = CLOSEUP_DIM
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        veil.fill((level, level, level))
        # Vinyetin merkezi **yuz**, ekranin ortasi degil: kafa kadrajin
        # ust yarisinda duruyor ve ekran merkezine odaklanan bir vinyet
        # tam da yuzu karartiyordu.
        face_y = big.get_height() // 4
        hole = radial_glow(CLOSEUP_VIGNETTE, (level, level, level), peak=1.0)
        veil.blit(hole, (INTERNAL_WIDTH // 2 - CLOSEUP_VIGNETTE,
                         face_y - CLOSEUP_VIGNETTE),
                  special_flags=pygame.BLEND_RGB_SUB)
        surface.blit(veil.convert(), (0, 0), special_flags=pygame.BLEND_RGB_SUB)

    # --- Gecisler -----------------------------------------------------------
    def _draw_fade(self, surface: pygame.Surface, panel: Panel) -> None:
        """Panel basinda siyahtan acilma, sonunda siyaha kapanma.

        Siddet **renkle** veriliyor, alfayla degil - `BLEND_RGB_SUB`
        alfayi yok sayiyor (`glow.py` basligi; proje bu tuzaga uc kez
        dustu).
        """
        fade_in = getattr(panel, "fade_in", 0)
        fade_out = getattr(panel, "fade_out", 0)
        amount = 0.0
        if fade_in > 0 and self.panel_frames < fade_in:
            amount = 1.0 - self.panel_frames / fade_in
        if fade_out > 0:
            left = panel.frames - self.panel_frames
            if 0 <= left < fade_out:
                amount = max(amount, 1.0 - left / fade_out)
        if amount <= 0.01:
            return
        level = int(255 * min(1.0, amount))
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        veil.fill((level, level, level))
        surface.blit(veil.convert(), (0, 0),
                     special_flags=pygame.BLEND_RGB_SUB)

    def _draw_actors(self, surface: pygame.Surface,
                     offset: tuple[int, int]) -> None:
        """Aktorler **y'ye gore** ciziliyor: onde duran ustte.

        Isik varsa en parlagi kenar isigi icin kullaniliyor - iki isik
        arasinda kalan bir karakteri iki kez konturlamak siluet
        okunurlugunu bozar.
        """
        key = self._brightest_light()
        for name in sorted(self.actor_order,
                           key=lambda n: self.actors[n].y):
            self.actors[name].draw(surface, offset, key)

    def _brightest_light(self) -> tuple[int, int, palette.RGB] | None:
        if not self.lights:
            return None
        x, y, _radius, colour, _peak = max(self.lights,
                                           key=lambda item: item[4])
        return (x, y, colour)

    def _draw_lights(self, surface: pygame.Surface,
                     offset: tuple[int, int]) -> None:
        ox, oy = offset
        for x, y, radius, colour, peak in self.lights:
            if radius <= 0 or peak <= 0.0:
                continue
            glow = radial_glow(radius, colour, peak=peak)
            surface.blit(glow, (x - ox - radius, y - oy - radius),
                         special_flags=pygame.BLEND_RGB_ADD)

    def _draw_vignette(self, surface: pygame.Surface) -> None:
        """Kenarlari karartir, ortayi birakir. Tek yuzey, tek gecis.

        **Siddet renkle ayarlaniyor, alfayla DEGIL.** `glow.py`'nin
        basliginda yazan kural: `BLEND_RGB_SUB`/`ADD` alfayi agirlik
        olarak kullanmaz. Ilk surumde `set_alpha()` ile denendi ve
        `vignette` degeri ne olursa olsun ekran **tamamen** karardi -
        Muhur ve El sahneleri iki noktaya dustu. Proje bu tuzaga
        ucuncu kez dusmus oldu; bu yorum dorduncusu icin duruyor.
        """
        amount = int(255 * max(0.0, min(1.0, self.vignette)))
        if amount <= 0:
            return
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        veil.fill((amount, amount, amount))
        # Ortadaki delik: ayni siddetteki haleyi veilden CIKARIYORUZ,
        # yani merkez sifira iniyor ve oraya hic karartma uygulanmiyor.
        radius = max(INTERNAL_WIDTH, INTERNAL_HEIGHT) // 2
        hole = radial_glow(radius, (amount, amount, amount), peak=1.0)
        veil.blit(hole, (INTERNAL_WIDTH // 2 - radius,
                         INTERNAL_HEIGHT // 2 - radius),
                  special_flags=pygame.BLEND_RGB_SUB)
        surface.blit(veil.convert(), (0, 0),
                     special_flags=pygame.BLEND_RGB_SUB)

    def _draw_flash(self, surface: pygame.Surface) -> None:
        if self.flash_strength <= 0.01:
            return
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        colour = palette.role("hit_flash")
        veil.fill(tuple(int(c * self.flash_strength) for c in colour))
        surface.blit(veil.convert(), (0, 0),
                     special_flags=pygame.BLEND_RGB_ADD)

    def _draw_extra_shake(self, surface: pygame.Surface) -> None:
        if self.extra_shake < 0.5:
            return
        ox = int(math.sin(self.shake_seed * 1.9) * self.extra_shake)
        oy = int(math.cos(self.shake_seed * 2.7) * self.extra_shake)
        surface.scroll(ox, oy)

    # --- Alt sinif kancalari ------------------------------------------------
    def _blit_panel_art(self, surface: pygame.Surface,
                        panel: Panel) -> bool:
        """`assets/panels/<sahne>_<panel>.png` varsa cizer.

        Ad **sahne sinifindan ve panel adindan** turuyor, elle
        eslestirme tablosu yok: bir tablo tutmak "dosya var ama tablo
        unutuldu" hatasini davet ederdi ve o hata sessiz olurdu.

            SourceCinematic + "cevap"  ->  source_cevap.png

        480x270 bekleniyor (ic cozunurluk). Baska boyut da ciziliyor
        ama olcegi kayar - `tools/import_art.py --tur panel` dogru
        boyutu zaten veriyor.
        """
        name = f"{panel_prefix(type(self))}_{panel.name}"
        art = panel_art(name)
        if art is None:
            return False
        surface.blit(art, (0, 0))
        return True

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Aktorlerin ARKASI. Varsayilan: bos (sahne rengi kaliyor)."""

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Aktorlerin ONU - kaya cikintisi, gecit kenari, sis."""

    def on_stage_panel(self, panel: Panel) -> None:
        """Panel basladi. Cue'larla anlatilamayan seyler icin."""

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"aktor {len(self.actors)}  parcacik {self.particles.alive_count}"
            f"  isik {len(self.lights)}"]


# =============================================================================
# Elle cizilmis paneller
# =============================================================================
PANEL_DIR = Path(__file__).resolve().parents[2] / "assets" / "panels"

_panel_cache: dict[str, pygame.Surface | None] = {}


def _panel_key(class_name: str) -> str:
    """`SourceCinematic` -> `source`. Sinif adindan dosya onekine."""
    name = class_name.removesuffix("Cinematic")
    out: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index:
            out.append("_")
        out.append(char.lower())
    return "".join(out)


def panel_prefix(cls: type) -> str:
    """Panel dosyalarinin oneki: `<bolum>_<sahne>`.

    **Bolum numarasi sart.** Ilk surum yalnizca sinif adini
    kullaniyordu ve iki bolumde ayni adli sahne var:
    `chapter02.DescentCinematic` ile `chapter03.DescentCinematic`.
    Ikisi de `descent_*` uretiyordu - bugun panel adlari cakismiyor
    ama biri "giris" adinda bir panel eklediginde oteki bolumun
    gorseli **sessizce** oraya da girerdi.

    Sessiz cakismalar bu projede pahaliya ogrenildi (dil anahtarlari,
    ses adlari, `draw_extra`). Onek modulden turuyor: tahmin
    edilebilir ve carpisamaz.
    """
    module = cls.__module__.rsplit(".", 1)[-1]
    chapter = module.replace("_cinematics", "")
    return f"{chapter}_{_panel_key(cls.__name__)}"


def panel_art(name: str) -> pygame.Surface | None:
    """Panel gorseli - yoksa None (ve bir daha diske bakilmaz)."""
    if name in _panel_cache:
        return _panel_cache[name]
    from src.art import imported
    from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
    image = imported.load_art(PANEL_DIR / f"{name}.png", name,
                              expect=(INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              alpha=False)
    _panel_cache[name] = image
    return image


def clear_panel_cache() -> None:
    _panel_cache.clear()
