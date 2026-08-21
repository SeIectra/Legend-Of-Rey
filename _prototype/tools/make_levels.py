"""Bolum tasarim araci.

Bolumler ASCII olarak burada tasarlanir; script bunlari dogrular ve
`lore/data/levels/*.json` olarak yazar. JSON dosyalarini elle duzenleme.

    python tools/make_levels.py

Sozluk (bkz. lore/world/tilemap.py):
    .  bos          #  kati       =  tek yonlu platform
    b  arka duvar   ^  diken      H  merdiven
    ~  su           o  kirilabilir

-------------------------------------------------------------------------------
DIKEY TASARIM KURALI  (en cok hata yapilan yer)

Rey bir platformun *ustunde* durur, yani isgal ettigi satir platform
satirinin bir ustudur:

    satir 12   .....  <- Rey burada durur  ("basilabilir satir")
    satir 13   =====  <- platform

Olculen ziplama yuksekligi 3 tile. Yani bir basilabilir satirdan digerine en
fazla 3 satir cikilabilir:

    zemin tepesi 16 -> basilabilir 15
    platform tepesi 13 -> basilabilir 12     (15 - 12 = 3  OK)
    platform tepesi 10 -> basilabilir  9     ( 12 - 9 = 3  OK)
    platform tepesi  7 -> basilabilir  6     (  9 - 6 = 3  OK)

Kisayol: **platform tepeleri zemin tepesinden 3'er azalir.**
Platformu 3 satir yukari koymak (16 -> 12) 4 tile'lik bir sicrama demektir
ve erisilemez. Bu hata bir kez yapildi; `Level.validate()` artik yakaliyor.

YATAY: bosluklar en fazla 4 tile genisliginde; ardisik platformlar arasi en
fazla 5 tile. Olcum icin: python tools/measure_jump.py
-------------------------------------------------------------------------------
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "lore" / "data" / "levels"

WIDTH = 80


def rows_from(text: str) -> list[str]:
    return [line.ljust(WIDTH, ".")[:WIDTH]
            for line in text.strip("\n").split("\n")]


def level(level_id: str, **kwargs) -> dict:
    data = {"id": level_id}
    data.update(kwargs)
    return data


# =============================================================================
# ACT I - THE WAKING HOLLOW
# Rey silahsiz. Sirayla ogretilenler: yurumek, ziplamak, tuzaktan kacinmak,
# sirttan vurmak, ve nihayet Echobrand.
#         0    5   10   15   20   25   30   35   40   45   50   55   60   65   70   75
#         |....|....|....|....|....|....|....|....|....|....|....|....|....|....|....|....
# =============================================================================

# --- 1. Uyanis --------------------------------------------------------------
# Dusman yok, olum yok. Bosluklarin dibi kapali: dusen oyuncu iki tile asagi
# iner ve geri ziplar. Ilk bolumun isi ziplamayi ogretmek, cezalandirmak degil.
# Zemin tepesi 16 -> platform tepeleri 13, 10, 7
ACT1_01 = """
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
........................=====...................................................
................................................................................
................................................................................
..............................=====.............................................
................................................................................
................................................................................
......................=====.....................................................
.......bbbbb................bbbbbbbbbb..........................bbbbbbb.........
.......bbbbb................bbbbbbbbbb..........................bbbbbbb.........
################...####################....#####################################
################...####################....#####################################
################################################################################
################################################################################
"""

# --- 2. Bos Eller -----------------------------------------------------------
# Ilk goblinler. Yavas yaklas, arkadan vur: tek vurusta duser.
# Zemin tepesi 14 -> platform tepeleri 11, 8
ACT1_02 = """
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................=====...........................................................
................................................................................
................................................................................
..........=====................................=====............................
.....bbbbbbbb...........bbbbbbbbbbbb..........................bbbbbbbbbbbb......
.....bbbbbbbb...........bbbbbbbbbbbb..........................bbbbbbbbbbbb......
######################...###############################...#####################
######################...###############################...#####################
################################################################################
################################################################################
"""

# --- 3. Dis Sirasi ----------------------------------------------------------
# Diken korosu. Bosluklarin dibinde diken var ama zemin kapali: dusersen bir
# kalp kaybedip geri ziplarsin, olmezsin.
# Zemin tepesi 13 -> platform tepeleri 10, 7
ACT1_03 = """
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
.............=====..................=====.......................................
................................................................................
................................................................................
.......=====....................=====...........................................
................................................................................
.....bbbb................................................bbbbbbbbbbbbbb.........
#######....#########....#########....#########....##############################
#######^^^^#########^^^^#########^^^^#########^^^^##############################
################################################################################
################################################################################
################################################################################
"""

# --- 4. Sayica Ustun --------------------------------------------------------
# Gercek ucurumlar burada basliyor: 4 tile genis, dibi acik.
# Zemin tepesi 13 -> platform tepeleri 10, 7
ACT1_04 = """
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
................................................................................
............=====...............................................................
................................................................................
................................................................................
.......=====....................................=====...........................
................................................................................
.....bbbbbbbbbbb............................o..o.........bbbbbbbbbbbbbbbbb......
################....############################....############################
################....############################....############################
################....############################....############################
################....############################....############################
"""

# --- 5. Echobrand -----------------------------------------------------------
# Zindanin dibi: kilic, atilma ve ilk gercek savas.
# Zemin tepesi 13 -> platform tepeleri 10, 7
ACT1_05 = """
................................................................................
................................................................................
................................................................................
..............bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
..............bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
..............bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
..............bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
..............bbbbbbbbbb=====bbbbbbbbbbbbbbbbb=====bbbbbbbbbbbbbbbbbbb..........
..............bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
..............bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
.......=====..bbbbbbbb=====bbb=====bbbbbbb=====bbbbbbbbbbbbbbbbbbbbbbb..........
..............bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
.....bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.........
################################################################################
################################################################################
################################################################################
################################################################################
"""

# --- 5b. The Gaoler (boss arenasi) -------------------------------------------
# Act I finali. Duz, tek katli bir oda - AI'nin kenar sezinlemesiyle
# ugrasmasi gerekmez, kovalamaca fazinda oyuncuya kacacak yer birakir.
# Zemin tepesi 12 -> basilabilir 11
ACT1_05_BOSS = """
................................................................................
................................................................................
................................................................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb............................................
................................................................................
################################################################################
################################################################################
################################################################################
"""


LEVELS = [
    level(
        "act1_01",
        name="Uyanis",
        act=1, theme="hollow", weather="none",
        music="assets/background_music.wav",
        rows=rows_from(ACT1_01),
        spawn=[4, 15],
        intro="Cael'in sesi: Kalk Rey. Ardo'yu aldilar.",
        entities=[],
        props=[
            {"type": "shrine", "x": 7, "y": 15, "id": "act1_01_shrine"},
            {"type": "torch", "x": 12, "y": 15},
            {"type": "torch", "x": 34, "y": 15},
            {"type": "chest", "x": 26, "y": 6, "contents": "essence",
             "amount": 8, "id": "act1_01_chest"},
            {"type": "torch", "x": 60, "y": 15},
            {"type": "door", "x": 74, "y": 15, "target": "act1_02"},
        ],
        next="act1_02",
    ),
    level(
        "act1_02",
        name="Bos Eller",
        act=1, theme="hollow", weather="none",
        rows=rows_from(ACT1_02),
        spawn=[3, 13],
        intro="Silahin yok. Yavas yaklas, arkadan vur.",
        entities=[
            {"type": "grunt", "x": 14, "y": 13, "patrol": 40, "facing": -1},
            {"type": "grunt", "x": 44, "y": 13, "patrol": 60, "facing": 1},
        ],
        props=[
            {"type": "torch", "x": 8, "y": 13},
            {"type": "torch", "x": 34, "y": 13},
            {"type": "chest", "x": 18, "y": 7, "contents": "essence",
             "amount": 10, "id": "act1_02_chest"},
            {"type": "torch", "x": 66, "y": 13},
            {"type": "door", "x": 74, "y": 13, "target": "act1_03"},
        ],
        next="act1_03",
    ),
    level(
        "act1_03",
        name="Dis Sirasi",
        act=1, theme="hollow", weather="none",
        rows=rows_from(ACT1_03),
        spawn=[2, 12],
        intro="Asagi bakma. Ustunden gec.",
        entities=[
            {"type": "wisp", "x": 30, "y": 8, "patrol": 60},
            {"type": "grunt", "x": 62, "y": 12, "patrol": 20},
        ],
        props=[
            {"type": "shrine", "x": 4, "y": 12, "id": "act1_03_shrine"},
            {"type": "torch", "x": 6, "y": 12},
            {"type": "torch", "x": 58, "y": 12},
            {"type": "door", "x": 74, "y": 12, "target": "act1_04"},
        ],
        next="act1_04",
    ),
    level(
        "act1_04",
        name="Sayica Ustun",
        act=1, theme="hollow", weather="none",
        rows=rows_from(ACT1_04),
        spawn=[3, 12],
        intro="Ucu birden. Kacmak da bir cozumdur.",
        entities=[
            {"type": "grunt", "x": 26, "y": 12, "patrol": 40},
            {"type": "grunt", "x": 40, "y": 12, "patrol": 40},
            {"type": "archer", "x": 62, "y": 12, "patrol": 14, "facing": -1},
        ],
        props=[
            {"type": "torch", "x": 8, "y": 12},
            {"type": "chest", "x": 14, "y": 6, "contents": "heart_shard",
             "id": "act1_04_shard"},
            {"type": "torch", "x": 38, "y": 12},
            {"type": "torch", "x": 68, "y": 12},
            {"type": "door", "x": 74, "y": 12, "target": "act1_05"},
        ],
        next="act1_05",
    ),
    level(
        "act1_05",
        name="Echobrand",
        act=1, theme="hollow", weather="none",
        rows=rows_from(ACT1_05),
        spawn=[3, 12],
        intro="Cael: Su tasin ustunde. Al onu.",
        entities=[
            {"type": "grunt", "x": 40, "y": 12, "patrol": 30},
            {"type": "grunt", "x": 52, "y": 12, "patrol": 24},
            {"type": "skeleton", "x": 64, "y": 12, "patrol": 20},
        ],
        props=[
            {"type": "shrine", "x": 6, "y": 12, "id": "act1_05_shrine"},
            {"type": "torch", "x": 18, "y": 12},
            {"type": "chest", "x": 24, "y": 12, "contents": "blade",
             "id": "act1_05_blade"},
            {"type": "torch", "x": 46, "y": 12},
            {"type": "chest", "x": 32, "y": 9, "contents": "dash",
             "id": "act1_05_dash"},
            {"type": "torch", "x": 68, "y": 12},
            {"type": "door", "x": 74, "y": 12, "target": "act1_05_boss",
             "boss": True},
        ],
        next="act1_05_boss",
    ),
    level(
        "act1_05_boss",
        name="The Gaoler",
        act=1, theme="hollow", weather="none",
        rows=rows_from(ACT1_05_BOSS),
        spawn=[4, 11],
        intro="Kudretli bir kukreme yankilanir.",
        entities=[
            {"type": "gaoler", "x": 28, "y": 11},
        ],
        props=[
            {"type": "torch", "x": 6, "y": 11},
            {"type": "torch", "x": 20, "y": 11},
            {"type": "torch", "x": 32, "y": 11},
            {"type": "door", "x": 36, "y": 11, "target": "", "locked": True},
        ],
        next="",
    ),
]


def main() -> int:
    from lore.world.level import Level, LevelDef

    OUT.mkdir(parents=True, exist_ok=True)
    failed = False

    for data in LEVELS:
        widths = {len(r) for r in data["rows"]}
        if len(widths) != 1:
            print(f"[!] {data['id']}: satir genislikleri farkli: {sorted(widths)}")
            failed = True
            continue

        problems = Level(LevelDef.from_dict(data)).validate()
        status = "OK " if not problems else "!! "
        print(f"{status}{data['id']:10s} {len(data['rows'][0])}x{len(data['rows'])} "
              f"dusman={len(data['entities'])} prop={len(data['props'])}")
        for problem in problems:
            print(f"     - {problem}")
            failed = True

        (OUT / f"{data['id']}.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    if failed:
        print("\nBazi bolumlerde sorun var - yukaridaki uyarilara bak.")
        return 1
    print(f"\n{len(LEVELS)} bolum dogrulandi ve yazildi -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
