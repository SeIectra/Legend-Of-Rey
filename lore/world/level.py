"""Seviye tanimi ve yukleyicisi.

Seviyeler JSON dosyalaridir; kod icinde tek bir bolum tanimi yoktur. Eski
yapida yeni bolum eklemek `level.py` icine yeni bir `elif` yazmak demekti -
28 bolumluk bir oyunda bu surdurulemez.

Harita ASCII olarak yazilir. Bir bolumu duz metin olarak gormek, tasarim
hatalarini (erisilemeyen platform, cok dar gecit, tuzak yigilmasi) daha yazarken
yakalatiyor.

Sozluk icin bkz. `world/tilemap.py::LEGEND`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pygame

from lore.constants import TILE
from lore.core.paths import resource
from lore.world.tilemap import TileMap


@dataclass
class LevelDef:
    """Bir bolumun ham tanimi (henuz nesnelere donusmemis)."""

    id: str
    name: str = ""
    act: int = 1
    theme: str = "hollow"
    weather: str = "none"
    music: str = ""
    rows: list[str] = field(default_factory=list)
    spawn: tuple[int, int] = (2, 2)
    entities: list[dict] = field(default_factory=list)
    props: list[dict] = field(default_factory=list)
    triggers: list[dict] = field(default_factory=list)
    intro: str = ""
    next_level: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LevelDef":
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", ""),
            act=int(data.get("act", 1)),
            theme=data.get("theme", "hollow"),
            weather=data.get("weather", "none"),
            music=data.get("music", ""),
            rows=list(data.get("rows", [])),
            spawn=tuple(data.get("spawn", (2, 2))),
            entities=list(data.get("entities", [])),
            props=list(data.get("props", [])),
            triggers=list(data.get("triggers", [])),
            intro=data.get("intro", ""),
            next_level=data.get("next", ""),
        )


class LevelIndex:
    """data/levels altindaki tum bolumleri bulur ve onbellekler."""

    def __init__(self) -> None:
        self._cache: dict[str, LevelDef] = {}
        self._order: list[str] = []
        self._scan()

    def _scan(self) -> None:
        directory = resource("lore", "data", "levels")
        if not directory.is_dir():
            print(f"[level] bolum dizini yok: {directory}")
            return
        for path in sorted(directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                print(f"[level] {path.name} okunamadi: {exc}")
                continue
            level = LevelDef.from_dict(data)
            self._cache[level.id] = level
            self._order.append(level.id)

    def get(self, level_id: str) -> LevelDef | None:
        return self._cache.get(level_id)

    def first(self) -> str:
        return self._order[0] if self._order else ""

    def next_after(self, level_id: str) -> str:
        """Bolumun `next` alani bossa dosya sirasindaki sonrakine gecer."""
        level = self._cache.get(level_id)
        if level and level.next_level:
            return level.next_level
        if level_id in self._order:
            index = self._order.index(level_id)
            if index + 1 < len(self._order):
                return self._order[index + 1]
        return ""

    def all_ids(self) -> list[str]:
        return list(self._order)

    def by_act(self, act: int) -> list[str]:
        return [i for i in self._order if self._cache[i].act == act]


class Level:
    """Yuklenmis, oynanabilir bir bolum."""

    def __init__(self, definition: LevelDef) -> None:
        self.definition = definition
        self.id = definition.id
        self.name = definition.name
        self.act = definition.act
        self.theme = definition.theme
        self.tilemap = TileMap.from_ascii(definition.rows, definition.theme)

    @property
    def spawn_point(self) -> tuple[float, float]:
        tx, ty = self.definition.spawn
        # Tile koordinatini piksele cevirirken ayagi tile'in tabanina koy.
        return (tx * TILE + TILE * 0.5, (ty + 1) * TILE)

    @property
    def bounds(self) -> pygame.Rect:
        return self.tilemap.bounds

    def entity_spawns(self) -> list[tuple[str, float, float, dict]]:
        out = []
        for entry in self.definition.entities:
            kind = entry.get("type", "grunt")
            tx = float(entry.get("x", 0))
            ty = float(entry.get("y", 0))
            options = {k: v for k, v in entry.items() if k not in ("type", "x", "y")}
            out.append((kind, tx * TILE + TILE * 0.5, (ty + 1) * TILE, options))
        return out

    def prop_spawns(self) -> list[tuple[str, float, float, dict]]:
        out = []
        for entry in self.definition.props:
            kind = entry.get("type", "torch")
            tx = float(entry.get("x", 0))
            ty = float(entry.get("y", 0))
            options = {k: v for k, v in entry.items() if k not in ("type", "x", "y")}
            out.append((kind, tx * TILE + TILE * 0.5, (ty + 1) * TILE, options))
        return out

    def validate(self) -> list[str]:
        """Tasarim hatalarini erken yakalar. Gelistirme sirasinda cagrilir."""
        problems: list[str] = []
        tm = self.tilemap
        if tm.w < 4 or tm.h < 4:
            problems.append("harita cok kucuk")

        sx, sy = self.definition.spawn
        if not (0 <= sx < tm.w and 0 <= sy < tm.h):
            problems.append(f"dogus noktasi harita disinda: {sx},{sy}")
        elif tm.is_solid(sx, sy):
            problems.append(f"dogus noktasi katı tile icinde: {sx},{sy}")

        for entry in self.definition.entities:
            ex, ey = int(entry.get("x", 0)), int(entry.get("y", 0))
            if not (0 <= ex < tm.w and 0 <= ey < tm.h):
                problems.append(f"dusman harita disinda: {entry}")
            elif tm.ground_below(ex, ey) is None and entry.get("type") != "wisp":
                problems.append(f"dusmanin altinda zemin yok: {entry}")

        has_exit = any(p.get("type") == "door" for p in self.definition.props)
        if not has_exit and not self.definition.next_level:
            problems.append("cikis kapisi ve `next` alani yok - bolum bitirilemez")

        problems.extend(self._check_gaps())
        problems.extend(self._check_reachability())
        return problems

    # Ziplama zarfi. Bu degerler tahmin degil, olcum:
    #     python tools/measure_jump.py
    # Su an motor 60 px (3.75 tile) yukseklik ve 92 px (5.75 tile) menzil
    # veriyor. Tasarim sinirlarini marj birakarak bunun altinda tutuyoruz -
    # kenardan kenara tam zamanlama istemek adil bir bolum tasarimi degildir.
    # JUMP_SPEED veya RUN_SPEED degisirse olcumu tekrarla ve buradan guncelle.
    MAX_JUMP_TILES = 4          # yatay
    MAX_JUMP_HEIGHT_TILES = 3   # dikey

    def _check_gaps(self) -> list[str]:
        """Ziplanamayacak genislikte bosluk var mi?

        Her sutun icin en ustteki basilabilir yuzeyi buluyoruz; hic yuzeyi
        olmayan ardisik sutunlar bir ucurumdur. Ucurum azami ziplama
        mesafesini asiyorsa bolum gecilemez demektir - bunu oyunda degil
        burada yakalamak gerekir.
        """
        tm = self.tilemap
        surface_missing: list[bool] = []
        for tx in range(tm.w):
            found = any(tm.is_solid(tx, ty) or tm.is_platform(tx, ty)
                        for ty in range(tm.h))
            surface_missing.append(not found)

        problems: list[str] = []
        run_start = None
        for tx, missing in enumerate([*surface_missing, False]):
            if missing and run_start is None:
                run_start = tx
            elif not missing and run_start is not None:
                width = tx - run_start
                # Haritanin iki ucundaki bosluklar kenar, ucurum degil.
                interior = run_start > 0 and tx < tm.w
                if interior and width > self.MAX_JUMP_TILES:
                    problems.append(
                        f"ziplanamaz ucurum: x={run_start}..{tx - 1} "
                        f"({width} tile, azami {self.MAX_JUMP_TILES})")
                run_start = None
        return problems

    # --- Erisilebilirlik ----------------------------------------------------
    def _standable(self) -> set[tuple[int, int]]:
        """Uzerinde durulabilen tile'lar: alti zemin, kendisi ve ustu bos.

        Ustu de bos olmali - Rey 20 piksel, yani bir tile'dan uzun; tavani
        alcak bir bosluga sigmaz.
        """
        tm = self.tilemap
        cells: set[tuple[int, int]] = set()
        for ty in range(tm.h - 1):
            for tx in range(tm.w):
                below = tm.at(tx, ty + 1)
                if below not in (1, 2, 7):          # SOLID, PLATFORM, BREAKABLE
                    continue
                if tm.is_solid(tx, ty) or tm.is_solid(tx, ty - 1):
                    continue
                cells.add((tx, ty))
        return cells

    def _path_clear(self, ax: int, ay: int, bx: int, by: int) -> bool:
        """Iki tile arasinda kaba bir gorus hatti - duvarin icinden gecmeyelim."""
        tm = self.tilemap
        steps = max(abs(bx - ax), abs(by - ay))
        if steps == 0:
            return True
        for i in range(1, steps + 1):
            t = i / steps
            cx = round(ax + (bx - ax) * t)
            cy = round(ay + (by - ay) * t)
            if tm.is_solid(cx, cy):
                return False
        return True

    def _check_reachability(self) -> list[str]:
        """Dogus noktasindan ziplayarak nereye varilabilir?

        Standable tile'lar uzerinde bir graf kurup dogus noktasindan BFS
        yapiyoruz. Kenar kurali ziplama zarfi: yatayda MAX_JUMP_TILES,
        yukari dogru MAX_JUMP_HEIGHT_TILES, asagi dogru sinirsiz (dusmek
        her zaman mumkun).

        Bu, "platformu koydum ama oraya cikilamiyor" hatasini yakalar -
        oyunu acmadan.
        """
        cells = self._standable()
        if not cells:
            return ["haritada uzerinde durulabilecek hicbir yer yok"]

        sx, sy = self.definition.spawn
        start = min(cells, key=lambda c: (abs(c[0] - sx) + abs(c[1] - sy)))
        if abs(start[0] - sx) + abs(start[1] - sy) > 3:
            return [f"dogus noktasi ({sx},{sy}) zeminden uzak"]

        reach = {start}
        queue = [start]
        max_up = self.MAX_JUMP_HEIGHT_TILES
        # MAX_JUMP_TILES *bosluk genisligi*. N tile genisligindeki bir boslugu
        # asmak, kenardaki iki basilabilir tile arasinda N+1 tile yol almak
        # demek - bu ikisini karistirmak "kapiya ulasilamiyor" gibi yanlis
        # uyarilar uretiyordu.
        max_dx = self.MAX_JUMP_TILES + 1
        while queue:
            cx, cy = queue.pop()
            for tx, ty in cells:
                if (tx, ty) in reach:
                    continue
                dx, dy = tx - cx, ty - cy
                if abs(dx) > max_dx:
                    continue
                if dy < -max_up:            # Cok yuksek
                    continue
                if not self._path_clear(cx, cy, tx, ty):
                    continue
                reach.add((tx, ty))
                queue.append((tx, ty))

        problems: list[str] = []
        # Onemli olan: etkilesimli prop'lara ve dusmanlara ulasilabiliyor mu?
        for entry in self.definition.props:
            px, py = int(entry.get("x", 0)), int(entry.get("y", 0))
            if entry.get("type") in ("torch",):      # Dekor, ulasilmasi gerekmez
                continue
            if not any(abs(px - rx) <= 1 and abs(py - ry) <= 1
                       for rx, ry in reach):
                problems.append(
                    f"erisilemez {entry.get('type')}: ({px},{py}) - "
                    f"dogus noktasindan ziplayarak varilamiyor")

        unreachable = len(cells) - len(reach)
        if unreachable > 0:
            sample = sorted(c for c in cells if c not in reach)[:4]
            problems.append(
                f"{unreachable} erisilemez zemin tile'i, ornek: {sample} "
                f"(azami ziplama {max_up} tile yukari, {max_dx} tile yana)")
        return problems
