"""Isik durumu - Bolum 3'un uc yeni mekaniginin ucu de buna dayaniyor.

`EchoState`/`Compass` ile ayni kucuk, tek-sorumluluklu desen: sahne basina
bir `LightState`, aktif isik kaynaklarini tutar ve tek bir soruya cevap
verir - **"bu nokta aydinlik mi?"** Bolum 3'ten once meselede hicbir
gameplay karsiligi yoktu (`cave_backdrop.draw_torches` sadece ciziyordu);
simdi Golge Suruklenen'in donma/vurulabilirlik durumu, mangal mekanigi ve
Mor Alev'in "golge dusmanlar yaklasamaz" ozelligi hepsi buradan okuyor.

Kaynaklar iki turlu:
  * **Statik** - duvar yuvalari, mangal, Mor Alev kaidesi. Oda kurulurken
    bir kez eklenir, yanip sonmesi disinda degismez.
  * **Tasinan** - oyuncunun elindeki mesale/Mor Alev. Her karede konumu
    guncellenir (`update_carried`).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LightSource:
    """Tek bir isik kaynagi. `key` sonradan bulup kaldirmak icin."""

    x: float
    y: float
    radius: float
    key: str = ""


class LightState:
    """Bir sahnedeki tum aktif isik kaynaklari."""

    def __init__(self) -> None:
        self._static: dict[str, LightSource] = {}
        self._carried: LightSource | None = None

    # --- Statik kaynaklar (yuvalar, mangal, Mor Alev kaidesi) ---------------
    def set_static(self, key: str, x: float, y: float, radius: float) -> None:
        self._static[key] = LightSource(x, y, radius, key)

    def remove_static(self, key: str) -> None:
        self._static.pop(key, None)

    def remove_prefix(self, prefix: str) -> None:
        """Adi bu onekle baslayan butun kaynaklari siler.

        Bolum 11'in isini yol boyunca **onlarca** kaynak yaziyor
        (`beam.apply_light`) ve her karede yeniden iziyor. Tek tek
        silmek cagirana sozlugun ic yapisini bildirirdi.
        """
        for key in [k for k in self._static if k.startswith(prefix)]:
            del self._static[key]

    def has_static(self, key: str) -> bool:
        return key in self._static

    # --- Tasinan kaynak (mesale/Mor Alev elde) -------------------------------
    def set_carried(self, x: float, y: float, radius: float) -> None:
        self._carried = LightSource(x, y, radius, "carried")

    def clear_carried(self) -> None:
        self._carried = None

    @property
    def carrying(self) -> bool:
        return self._carried is not None

    # --- Sorgular -------------------------------------------------------------
    def _sources(self):
        if self._carried is not None:
            yield self._carried
        yield from self._static.values()

    def radius_at(self, x: float, y: float) -> float:
        """Bu noktadaki en genis kapsayan isigin yaricapi. Isik yoksa 0."""
        best = 0.0
        for source in self._sources():
            dx = x - source.x
            dy = y - source.y
            if dx * dx + dy * dy <= source.radius * source.radius:
                best = max(best, source.radius)
        return best

    def in_light(self, x: float, y: float) -> bool:
        return self.radius_at(x, y) > 0.0

    def all_sources(self) -> list[LightSource]:
        return list(self._sources())
