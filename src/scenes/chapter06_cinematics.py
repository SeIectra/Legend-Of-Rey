"""Bolum 6'nin giris sahnesi - "havali giris".

`docs/gdd.md` 10: *"6 | ARDO | **Havali giris**, ilk team-up, BOSS 1"*.
`docs/yapi.md` B6: *"Rey kosede sikisir, uc yaratik. Golge yukaridan
duser, ucunu bicer. Bakisma, soru isareti balonu."*

## Neden yeniden yazildi

Belgede yazan sahne kodda **yoktu**. `_rescue()` tek karede oluyordu:
yoldas doguyor, uc yaratik aninda oluyor, parcacik patliyor, bir soru
isareti beliriyor. Oyuncu hicbir seyi goremiyordu.

Arda (30.08.2026): *"Ardo ilk geldiginde bir sinematik ve diyalog
koyalim. Bahsettigin havali giris hic olmadi ve karakter tanitilmadi."*

Hakli, ve ikinci yarisi bir **tasarim degisikligi**: `docs/yapi.md`
B6'da *"Bakisma, soru isareti"* yaziyor, yani kelimesiz bir karsilasma.
Bu modul artik konusuyor. Gerekce Arda'nin: bir soru isareti kimin
geldigini soylemiyor, ve o an oyunun ikinci oynanabilir karakteriyle
tanisma ani.

**Yanki hala susuyor** - o satir korunuyor. `docs/gdd.md` 10: *"8 |
Ates Basi | Yanki ilk kez Ardo hakkinda konusur."* Burada konusan iki
karakterin kendisi.

## Roller kanondan

`docs/gdd.md` 3: *"Secmedigin, ara sahnelerde havali girisi yapan taraf
olur."* Yani sahne oynanan karaktere gore donuyor:

    Rey oynanirken   kosede sen varsin, dusen Ardo
    Ardo oynanirken  kosede sen varsin, dusen Rey

Aktor adlari bu yuzden `cornered` / `saviour` - kimin hangi sprite
oldugu `character`'dan turuyor. Iki ayri sahne yazmak ayni seyin iki
kopyasini bakim yuku yapardi (ayni gerekce `chapter07_cinematics.py`).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

GROUND_Y = 178
# Kosedeki oyuncunun yeri - sag duvara sikismis.
CORNERED_X = 336.0
# Dusen figurun basladigi yukseklik: ekranin USTUNDE, yani gorunmuyor.
DROP_FROM_Y = -40.0
DROP_TO_X = 268.0

# Uc yaratik. Konumlari oyuncuyla dusen figur ARASINDA: kurtaris
# gercekten aradaki seyi temizliyor, arkadan dolasmiyor.
CREATURE_X = (196.0, 232.0, 264.0)

# Inisin carpma karesi - hitstop. `CLAUDE.md` 7: olduruccu 12 kare.
# Bu uc dusmani birden bicen bir inis; en agir deger dogru olan.
LANDING_FREEZE = 12


class ArdoEntranceCinematic(StagedScene):
    """Golge yukaridan duser, ucunu bicer, dogrulur, konusur."""

    background = "void"
    # Bu bir konusma: paneller oyuncuyu bekliyor (`story.py`'nin
    # `wait_for_input` alani). Arda'nin 30.08 geri bildirimi:
    # *"Cumleler okunmuyor, kullanicinin bir tusa basmasi beklenmeli."*
    wait_for_input = True

    PANELS = (
        # A: kose. Uc yaratik yaklasiyor, oyuncu duvara yaslanmis.
        Panel(70, "kose", wait_for_input=False, cues=(
            Cue("cornered", state="idle", face=-1),
            Cue("creature0", state="run", face=1,
                move_to=(228.0, GROUND_Y), move_frames=64),
            Cue("creature1", state="run", face=1,
                move_to=(262.0, GROUND_Y), move_frames=64),
            Cue("creature2", state="run", face=1,
                move_to=(292.0, GROUND_Y), move_frames=64),
        )),
        # B: golge duser. **Hizlanarak** (`move_ease="in"`) - yer cekimi
        # yavaslamaz. Siluet: kim oldugu henuz belli degil.
        Panel(26, "dusus", wait_for_input=False, cues=(
            Cue("saviour", visible=True, silhouette=True, state="fall",
                face=-1, move_to=(DROP_TO_X, GROUND_Y), move_frames=24,
                move_ease="in"),
        )),
        # C: CARPMA. Hitstop + flas + sarsinti + toz, hepsi ayni karede.
        # `CLAUDE.md` 7: uclu senkron tek noktadan.
        Panel(34, "carpma", shake=4.0, wait_for_input=False, cues=(
            Cue("saviour", state="land", freeze=LANDING_FREEZE, flash=0.5,
                shake=4.0, burst="dust", burst_count=20,
                sound="hit_kill"),
            Cue("creature0", state="death", burst="blood", burst_count=14),
            Cue("creature1", state="death", burst="blood", burst_count=14),
            Cue("creature2", state="death", burst="blood", burst_count=14),
        )),
        # D: yaratiklar yok olur, figur dogrulur ve **isiga cikar**.
        Panel(52, "dogrulma", wait_for_input=False, cues=(
            Cue("creature0", visible=False),
            Cue("creature1", visible=False),
            Cue("creature2", visible=False),
            Cue("saviour", silhouette=False, state="idle", face=1,
                delay=10),
        )),
        # E-G: bakisma ve tanisma. Replikler `on_enter`'da doluyor -
        # kimin konustugu oynanan karaktere bagli.
        Panel(40, "bakisma", cues=(
            Cue("cornered", state="idle", face=-1),
            Cue("saviour", state="idle", face=1),
        )),
        Panel(40, "soru"),
        Panel(40, "isim"),
        # Tanisma bitti - **kim oldugu** yuzden okunsun. Bolum boyunca
        # bu karakteri 32 piksellik bir figur olarak gorecegiz; bir kez
        # yakindan gormek onu bir siluet olmaktan cikariyor.
        Panel(44, "yuz", closeup="saviour", fade_in=10, fade_out=10),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.saviour_key = other_character(character)
        self.ACTORS = self._build_actors()
        super().on_enter(**kwargs)
        self.vignette = 0.34
        # Mesale isigi kosede: sahnenin tek isik kaynagi ve oyuncunun
        # yaninda. Dusen figur karanliktan geliyor.
        self.add_light(int(CORNERED_X) - 30, GROUND_Y - 26, 58,
                       palette.color("ember_light"), peak=0.5)
        self.add_light(int(CORNERED_X) - 40, GROUND_Y - 32, 170,
                       palette.color("ember"), peak=0.19)
        self._write_dialogue()

    def _build_actors(self) -> tuple[ActorSpec, ...]:
        creatures = tuple(
            ActorSpec(f"creature{i}", "shambler", x, GROUND_Y, facing=1)
            for i, x in enumerate(CREATURE_X))
        return creatures + (
            ActorSpec("cornered", self.character, CORNERED_X, GROUND_Y,
                      facing=-1, scale=2),
            # Baslangicta **gorunmez ve ekranin ustunde**: ilk panelde
            # sahnede olmamali, yoksa surpriz kalmaz.
            ActorSpec("saviour", self.saviour_key, DROP_TO_X, DROP_FROM_Y,
                      facing=-1, scale=2, silhouette=True, visible=False),
        )

    def _write_dialogue(self) -> None:
        """Uc panele replik koyar. Kim konusuyorsa o.

        Anahtarlar **duz dize** - f-string ile kurulani `test_lang.py`
        goremiyor (proje bu tuzaga alti kereden fazla dustu).
        """
        if self.character == "ardo":
            # Ardo oynaniyor: dusen Rey, tanitilan Rey.
            beats = {
                "bakisma": Line("rey", "line.ch06_meet_rey_first"),
                "soru": Line("ardo", "line.ch06_meet_ardo_who"),
                "isim": Line("rey", "line.ch06_meet_rey_name"),
            }
        else:
            beats = {
                "bakisma": Line("ardo", "line.ch06_meet_ardo_first"),
                "soru": Line("rey", "line.ch06_meet_rey_who"),
                "isim": Line("ardo", "line.ch06_meet_ardo_name"),
            }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues)
            if p.name in beats else p
            for p in self.panels)

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name == "dusus":
            # **Ardo.mp3** - Arda'nin talimati: oteki karakterin
            # girislerinde bu parca. Girise ait, karaktere degil.
            self.game.music.hold("companion", 600, fade_ms=200)
            self.game.play_sound("swing_heavy")

    # --- Cizim --------------------------------------------------------------
    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_corner(surface, self.frame)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Soru isareti - `docs/gdd.md` 11'in B6 satiri.

        Replik geldi ama **soru isareti kaldi**: o, iki yabancinin
        arasindaki seyin isareti ve romantik yayin ilk halkasi. Iki
        govdenin ARASINDA duruyor, birinin tepesinde degil - ilk
        surumde oyuncunun uzerindeydi ve "oyuncu sasirdi" gibi
        okunuyordu.
        """
        if panel.name != "bakisma":
            return
        cornered = self.actor("cornered")
        saviour = self.actor("saviour")
        if cornered is None or saviour is None:
            return
        from src.ui import text as uitext
        mid_x = int((cornered.x + saviour.x) * 0.5)
        lift = 46 + int(math.sin(self.frame * 0.12) * 2)
        uitext.draw(surface, "?", mid_x, int(GROUND_Y) - lift,
                    palette.color("bone"), align="center", outline=True)

    def on_finished(self) -> None:
        self.scenes.pop()


def _draw_corner(surface: pygame.Surface, frame: int) -> None:
    """Cikmaz kose: sagda duvar, solda karanlik koridor.

    Sikismis olmak **gorunmeli**. Duz bir zemin cizilseydi oyuncu "neden
    kacmiyor" diye sorardi; duvar sahnenin bahanesi.

    Kenar cizgileri bilerek **yumusak**: ilk surumde zemin `stone`
    renginde tek piksellik bir cizgiydi ve neredeyse siyah bir arka
    planin uzerinde tel kafes gibi okunuyordu. Kontrasti bir kademe
    dusurmek onu bir yuzeyin kenari yapti.
    """
    surface.fill(palette.color("ink"))

    # Arka duvar - uzak, dalgali ust kenar.
    back = palette.color("stone_darkest")
    for x in range(0, INTERNAL_WIDTH, 4):
        top = 56 + int(math.sin(x * 0.019) * 10)
        surface.fill(back, (x, top, 4, GROUND_Y - top))

    # Kose duvari: sagda, tavandan zemine. Oyuncu buraya sikisti.
    wall_x = int(CORNERED_X) + 26
    surface.fill(palette.color("stone_dark"),
                 (wall_x, 34, INTERNAL_WIDTH - wall_x, GROUND_Y - 34))
    surface.fill(palette.color("stone"), (wall_x, 34, 1, GROUND_Y - 34))
    # Tas siralari - duvarin duz bir blok olmadigi okunsun. Sirali
    # kaydirma (satir basina 6 piksel) orgu hissi veriyor.
    for index, row in enumerate(range(34, GROUND_Y, 9)):
        offset = 6 if index % 2 else 0
        surface.fill(palette.color("stone_darkest"),
                     (wall_x + 2, row, INTERNAL_WIDTH - wall_x - 2, 1))
        surface.fill(palette.color("stone_darkest"),
                     (wall_x + 8 + offset, row, 1, 9))

    # Zemin
    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))
    surface.fill(palette.color("stone_darkest"),
                 (0, GROUND_Y + 1, INTERNAL_WIDTH, 2))
