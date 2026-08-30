"""Golge Suruklenen - Bolum 3 Oda 4.

`docs/bolum-03.md`: *"Sadece karanlikta var. Isiga girince donar ve
saldiramaz (ama olmez). Isiktan cikinca tekrar canlanir. Oldurmek icin
isikta dovmelisin."*

`Shambler`'dan turuyor - ayni ritim/poise/sayilar, ustune iki sey ekliyor:

  * **Karanlikta vurulmazlik** - `Boss.phase_armor`in ayni deseni
    (`entities/boss.py`): `take_damage` karanlikta `DamageResult(hit=False)`
    donuyor. Bu, "isikta dov" ogretisini bir tasarim notu olmaktan
    cikarip zorunlu bir kurala ceviriyor - yoksa oyuncu karanlikta da
    vurup gecebilirdi ve "meshaleyi yere koy, dar isik dairesinde dov"
    aha anini hic yasamazdi.
  * **Isikta donma** - `Climber.hanging`in ayni ruhu: durum makinesinin
    saldiri/yaklasma kismi atlanir (vx sifira yaklasir), ama sendeleme/
    can/animasyon normal isler - donmus haldeyken de vurulabilir olmasi
    gerekiyor.

Isik sorgusu `scene.light` (`systems/light.py`) uzerinden - Bolum 3 disinda
bir sahnede `light` yoksa (Chapter01/02) hicbir zaman aydinlik sayilmaz,
yani bu dusman yanlislikla baska bir bolumde kullanilirsa hep karanlikta
kalir (guvenli varsayilan, olduren degil).
"""
from __future__ import annotations

from src.combat.hitbox import DamageResult
from src.entities.enemies.shambler import Shambler
from src.entities.enemy import EnemyState


class ShadowShambler(Shambler):
    sprite_name = "shambler"
    body_colour = "violet_dark"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        # Karanlikta kac kez bosa vuruldu - sahne bunu okuyor.
        self.shrugged_off = 0

    @property
    def _in_light(self) -> bool:
        light = getattr(self.scene, "light", None)
        if light is None:
            return False
        return light.in_light(self.body.center_x, self.body.center_y)

    def take_damage(self, box, direction):
        if not self._in_light:
            # Karanlikta zirhli degil - **dokunulmaz**. Hasar hic islenmez,
            # sendeleme de yok; oyuncu bunun bir "direnc" degil bir "kural"
            # oldugunu vurustan hemen anlamali.
            #
            # `shrugged_off` sahnenin okudugu isaret: "oyuncu vurdu ve
            # hicbir sey olmadi". Bolum 11 bunu bir kez gorunce kurali
            # yaziyla da soyluyor - ders vurustan geliyor, yazi yalnizca
            # "oyun mu bozuk" sorusunu onluyor.
            self.shrugged_off += 1
            return DamageResult(hit=False)
        return super().take_damage(box, direction)

    def _think(self) -> None:
        if self._in_light and self.state is not EnemyState.STAGGER:
            self.body.approach_vx(0.0, 0.5)
            return
        super()._think()
