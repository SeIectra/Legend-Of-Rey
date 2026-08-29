"""Yetenek agaci dogrulamasi - `src/systems/skilltree.py`.

`docs/gdd.md` 6 baglayici: **3 dal x 4 seviye**. Buradaki kontroller kodun
calistigini degil, agacin bir **secim** olmaya devam ettigini koruyor:

  * Onkosul zinciri - seviye atlanamaz, yoksa dallarin karakteri kalmaz
  * Puan muhasebesi - yetmeyince acilmaz, acilinca duser, yarim kalmaz
  * Bedeller artan ve butce dar - agac asla tamamlanamaz
  * Etkiler carpan/bonus - `docs/dovus-sistemi.md`'nin taban degerlerine
    dokunulmuyor (CLAUDE.md 7)
  * ESKI KAYIT - `skill_points`/`skills` alanlarini hic bilmeyen bir kayit
    sorunsuz aciliyor

Pygame'e ihtiyaci yok: agac saf mantik, kayit saf veri.

Calistir:
    python tests/test_skilltree.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    ARDO_CHAIN_WINDOW, CHAIN_WINDOW_FRAMES, COMBO_THRESHOLD_MID,
    DODGE_IFRAMES, DODGE_TOTAL_FRAMES, REY_CHAIN_WINDOW, REY_DODGE_CHARGES,
    REY_MAX_HEALTH, SKILL_BRANCH_LEVELS,
)
from src.systems import skilltree as tree  # noqa: E402
from src.systems.echo import COMBO_TO_RESTORE  # noqa: E402
from src.systems.save import SaveData  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def near(value: float, want: float) -> bool:
    return abs(value - want) < 1e-6


# --- Sahte oyuncu -----------------------------------------------------------
# Kosullu etkiler oyuncunun O ANKI durumuna bakiyor (charms.py deseni).
# Gercek `Player` pygame ve sahne gerektirir; kosullar `getattr` ile
# okundugu icin bu kadari yetiyor.
class FakeCombo:
    def __init__(self, count: int = 0) -> None:
        self.count = count


class FakeChain:
    def __init__(self, busy: bool = False, is_finisher: bool = False) -> None:
        self.busy = busy
        self.is_finisher = is_finisher


class FakeEcho:
    def __init__(self, active: bool = True) -> None:
        self.active = active


class FakeScene:
    def __init__(self, echo: FakeEcho | None = None) -> None:
        self.echo = echo


class FakePlayer:
    def __init__(self, combo: int = 0, finisher: bool = False,
                 echo: FakeEcho | None = None) -> None:
        self.combo = FakeCombo(combo)
        self.chain = FakeChain(busy=finisher, is_finisher=finisher)
        self.scene = FakeScene(echo)


def fresh(points: int = 0, character: str = "rey") -> SaveData:
    return SaveData(character=character, skill_points=points)


def branch(key: str) -> tree.Branch:
    return next(b for b in tree.BRANCHES if b.key == key)


def main() -> int:
    # --- 1. Agacin sekli (BAGLAYICI - docs/gdd.md 6) ------------------------
    print("--- 3 dal x 4 seviye ---")
    check(len(tree.BRANCHES) == 3, "uc dal var", str(len(tree.BRANCHES)))
    for b in tree.BRANCHES:
        check(len(b.nodes) == SKILL_BRANCH_LEVELS,
              f"{b.key}: dort seviye", str(len(b.nodes)))
    check(len(tree.NODES) == 12, "on iki dugum, hepsi benzersiz",
          str(len(tree.NODES)))

    costs = [n.cost for n in branch("blade").nodes]
    check(costs == sorted(costs) and costs[-1] > costs[0],
          "bedeller artiyor - ust seviye ucuz degil", str(costs))
    branch_cost = sum(costs)
    check(branch_cost == 6, "bir dalin tamami 6 puan", str(branch_cost))
    check(tree.TOTAL_COST == 18, "agacin tamami 18 puan", str(tree.TOTAL_COST))
    # docs/ekonomi-uretim.md 1: oyun boyunca kabaca 6 yetenek puani.
    check(tree.TOTAL_COST > branch_cost * 2,
          "butce agaci tamamlamaya ASLA yetmez - secim gercek",
          f"butce ~6, agac {tree.TOTAL_COST}")

    print("\n--- seviye ve onkosul haritasi ---")
    for b in tree.BRANCHES:
        for level, node in enumerate(b.nodes, start=1):
            check(tree.level_of(node.key) == level,
                  f"{node.key}: seviye {level}")
            check(tree.branch_of(node.key) is b, f"{node.key}: dali dogru")
    check(tree.prerequisite(tree.BLADE_EDGE) is None,
          "ilk seviyenin onkosulu yok")
    check(tree.prerequisite(tree.BLADE_MOMENTUM).key == tree.BLADE_FLOW,
          "seviye 3'un onkosulu seviye 2")
    check(tree.get("yok_boyle_bir_sey") is None, "bilinmeyen dugum None")
    check(tree.label_key("yok_boyle_bir_sey") == "skill.unknown",
          "bilinmeyen dugum icin yedek dil anahtari")

    # --- 2. Onkosul zinciri (seviye ATLANAMAZ) ------------------------------
    print("\n--- onkosul: seviye atlanamaz ---")
    save = fresh(points=99)          # puan bol - tek engel onkosul olsun
    check(tree.can_unlock(save, tree.BLADE_EDGE),
          "seviye 1 puan varken alinabilir")
    check(not tree.can_unlock(save, tree.BLADE_FLOW),
          "seviye 2 alinamaz - seviye 1 kapali")
    check(not tree.can_unlock(save, tree.BLADE_MOMENTUM),
          "seviye 3 alinamaz - seviye 2 kapali")
    check(not tree.unlock(save, tree.BLADE_MOMENTUM),
          "onkosulsuz unlock reddediliyor")
    check(save.skill_points == 99 and not save.skills,
          "reddedilen unlock hicbir sey degistirmedi",
          f"{save.skill_points} puan, {save.skills}")

    tree.unlock(save, tree.BLADE_EDGE)
    check(tree.unlocked(save, tree.BLADE_EDGE), "seviye 1 acildi")
    check(tree.can_unlock(save, tree.BLADE_FLOW), "seviye 2 artik alinabilir")
    check(not tree.can_unlock(save, tree.BLADE_MOMENTUM),
          "seviye 3 HALA kilitli - iki seviye birden atlanmiyor")

    tree.unlock(save, tree.BLADE_FLOW)
    check(tree.can_unlock(save, tree.BLADE_MOMENTUM),
          "seviye 2 acilinca seviye 3 alinabilir")
    check(not tree.can_unlock(save, tree.BLADE_EDGE),
          "acik dugum tekrar alinamaz")
    check(not tree.unlock(save, tree.BLADE_EDGE),
          "ayni dugum iki kez acilmiyor")
    check(save.skills.count(tree.BLADE_EDGE) == 1,
          "kayitta tek kopya", str(save.skills))

    # Dallar birbirinden bagimsiz: bir dalda ilerlemek digerini acmiyor.
    check(not tree.unlocked(save, tree.STONE_HIDE)
          and tree.can_unlock(save, tree.STONE_HIDE),
          "diger dalin seviye 1'i hala kendi basina duruyor")
    check(not tree.can_unlock(save, tree.STONE_GUARD),
          "bir daldaki ilerleme digerinin onkosulunu saymiyor")

    # --- 3. Puan muhasebesi -------------------------------------------------
    print("\n--- puan muhasebesi ---")
    save = fresh(points=1)
    check(tree.available_points(save) == 1, "acilis puani")
    check(tree.spent_points(save) == 0, "hic harcanmadi")

    check(tree.unlock(save, tree.STONE_HIDE), "1 puanla seviye 1 acildi")
    check(tree.available_points(save) == 0, "puan dusdu",
          str(tree.available_points(save)))
    check(tree.spent_points(save) == 1, "harcanan 1")
    check(not tree.can_unlock(save, tree.STONE_GUARD),
          "puan bitince onkosulu saglayan dugum bile alinamaz")
    check(not tree.unlock(save, tree.STONE_GUARD), "puansiz unlock reddedildi")
    check(save.skills == [tree.STONE_HIDE],
          "reddedilen unlock kaydi kirletmedi", str(save.skills))

    # Pahali dugum: kalan puan bedelin ALTINDA olunca reddedilmeli.
    tree.grant_points(save, 1)
    tree.unlock(save, tree.STONE_GUARD)
    check(tree.available_points(save) == 0, "iki seviye, iki puan")
    tree.grant_points(save, 1)
    check(tree.NODES[tree.STONE_ROLL].cost == 2, "seviye 3 iki puan eder")
    check(not tree.can_unlock(save, tree.STONE_ROLL),
          "1 puan 2 puanlik dugume yetmiyor")
    tree.grant_points(save, 1)
    check(tree.unlock(save, tree.STONE_ROLL), "2 puan yeter")
    check(tree.available_points(save) == 0 and tree.spent_points(save) == 4,
          "muhasebe tutuyor", f"kalan 0, harcanan {tree.spent_points(save)}")

    # Tam butce senaryosu: 6 puan bir dali tam acar, geriye hicbir sey kalmaz.
    save = fresh(points=6)
    for node in branch("echo").nodes:
        tree.unlock(save, node.key)
    check(len(save.skills) == 4 and tree.available_points(save) == 0,
          "6 puan bir dali dibine kadar aciyor", str(save.skills))
    check(not tree.can_unlock(save, tree.BLADE_EDGE),
          "dal tamamlandiginda baska hicbir sey alinamiyor")
    check(len(tree.unlocked_nodes(save)) == 4, "unlocked_nodes dogru sayiyor")

    # --- 4. Etki toplayicilari (charms.py deseni) ---------------------------
    print("\n--- etkiler: carpanlar ---")
    idle = FakePlayer()
    check(near(tree.damage_scale([], idle), 1.0), "bos liste notr")
    check(near(tree.damage_scale(["yok_boyle_bir_sey"], idle), 1.0),
          "bilinmeyen anahtar yok sayiliyor")
    check(near(tree.damage_scale([tree.BLADE_EDGE], idle), 1.06),
          "BILEME kosulsuz %6",
          f"{tree.damage_scale([tree.BLADE_EDGE], idle):.4f}")

    low = FakePlayer(combo=COMBO_THRESHOLD_MID - 1)
    high = FakePlayer(combo=COMBO_THRESHOLD_MID)
    check(near(tree.damage_scale([tree.BLADE_MOMENTUM], low), 1.0),
          "IVME esigin altinda hicbir sey yapmiyor")
    check(near(tree.damage_scale([tree.BLADE_MOMENTUM], high), 1.15),
          "IVME 10+ combo'da %15")

    check(near(tree.damage_scale([tree.BLADE_FINISHER], idle), 1.0),
          "SON SOZ bostayken notr")
    check(near(tree.damage_scale([tree.BLADE_FINISHER],
                                 FakePlayer(finisher=True)), 1.25),
          "SON SOZ yalniz bitirici vurusta %25")

    # Carpanlar CARPILARAK birlesir, toplanarak degil (charms.py ile ayni
    # kural: "iki %15'lik %30 degil %32 verir"). Fark tam olarak capraz
    # terim kadar - toplama yazilsaydi bu kontrol kirilirdi.
    both = tree.damage_scale([tree.BLADE_EDGE, tree.BLADE_MOMENTUM], high)
    check(near(both, 1.06 * 1.15), "carpanlar carpilarak birlesiyor",
          f"{both:.4f} = 1.06 x 1.15")
    check(near(both - (1.0 + 0.06 + 0.15), 0.06 * 0.15),
          "toplama DEGIL - fark tam capraz terim kadar",
          f"{both:.4f} != {1.0 + 0.06 + 0.15:.4f}")

    print("\n--- etkiler: savunma ---")
    check(near(tree.defence_scale([tree.STONE_GUARD], idle), 0.94),
          "KORUMA alinan hasari %6 azaltiyor")
    check(near(tree.defence_scale([tree.STONE_WILL], idle), 0.92),
          "IRADE alinan hasari %8 azaltiyor")
    check(near(tree.defence_scale([tree.STONE_GUARD, tree.STONE_WILL], idle),
               0.94 * 0.92), "iki koruma carpilarak birlesiyor")
    check(tree.defence_scale([tree.STONE_GUARD, tree.STONE_WILL], idle) > 0.8,
          "yigilma dokunulmazliga gitmiyor")

    # SIPER yalniz Yanki ACIKKEN calisir - bedeli hafifletir, silmez.
    check(near(tree.defence_scale([tree.ECHO_WARD], idle), 1.0),
          "SIPER Yanki'siz oyuncuda notr (Ardo)")
    check(near(tree.defence_scale([tree.ECHO_WARD],
                                  FakePlayer(echo=FakeEcho(active=False))), 1.0),
          "SIPER Yanki kapaliyken notr")
    check(near(tree.defence_scale([tree.ECHO_WARD],
                                  FakePlayer(echo=FakeEcho(active=True))), 0.88),
          "SIPER Yanki acikken %12 koruma")

    print("\n--- etkiler: Yanki gorusu ---")
    seer = FakePlayer(echo=FakeEcho())
    check(near(tree.echo_sight_scale([tree.ECHO_REACH], seer), 1.25),
          "ERIM menzili %25 uzatiyor")
    check(near(tree.echo_sight_scale([tree.ECHO_REACH, tree.ECHO_GRIP], seer),
               1.25 * 1.30), "ERIM + KAVRAYIS carpilarak birlesiyor")
    check(near(tree.echo_sight_scale([tree.ECHO_REACH, tree.ECHO_GRIP], idle),
               1.0), "Yanki'si olmayan karakterde menzil yetenegi notr")

    print("\n--- etkiler: duz bonuslar (toplanir) ---")
    check(tree.max_health_bonus([tree.STONE_HIDE]) == 5, "POST +5 can")
    check(tree.max_health_bonus([tree.STONE_HIDE, tree.STONE_WILL]) == 15,
          "duz bonuslar TOPLANIYOR - carpilmiyor",
          str(tree.max_health_bonus([tree.STONE_HIDE, tree.STONE_WILL])))
    check(tree.chain_window_bonus([tree.BLADE_FLOW]) == 2, "AKIS +2 kare")
    check(tree.dodge_charge_bonus([tree.STONE_ROLL]) == 1,
          "YUVARLANMA +1 kacinma hakki")
    check(tree.restore_combo_reduction([tree.ECHO_MEND]) == 6,
          "ONARIM 6 vurus indiriyor")
    check(COMBO_TO_RESTORE - tree.restore_combo_reduction([tree.ECHO_MEND])
          == 14, "Yanki 20 yerine 14 combo'da iyilesiyor")
    check(tree.max_health_bonus([]) == 0 and tree.chain_window_bonus([]) == 0,
          "yeteneksiz oyuncuya hicbir bonus sizmiyor")

    # --- 5. BAGLAYICI taban degerlere dokunulmadi (CLAUDE.md 7) -------------
    # Yetenekler taban degerlerin USTUNE biner. Bir gun biri "artik yetenek
    # var, tabani dusurelim" derse burasi kirilir - kasitli.
    print("\n--- taban degerler yerinde ---")
    check(CHAIN_WINDOW_FRAMES == 12, "zincir penceresi tabani 12 kare")
    check(REY_CHAIN_WINDOW == 14 and ARDO_CHAIN_WINDOW == 10,
          "Rey 14 / Ardo 10 - AKIS bunlari yeniden yazmiyor")
    check(REY_CHAIN_WINDOW + tree.chain_window_bonus([tree.BLADE_FLOW]) == 16,
          "AKIS tabanin USTUNE biniyor", "14 + 2 = 16")
    check(DODGE_IFRAMES == 6 and DODGE_TOTAL_FRAMES == 18,
          "kacinma 6/18 kare - YUVARLANMA sarj veriyor, zamanlama degil")
    check(REY_MAX_HEALTH == 80 and REY_DODGE_CHARGES == 2,
          "Rey'in taban can/sarj degerleri yerinde")
    check(all(node.chain_window >= 0 and node.max_health >= 0
              and node.dodge_charges >= 0 for node in tree.NODES.values()),
          "hicbir yetenek taban degeri DUSURMUYOR")

    # --- 6. Dal / karakter uyumu -------------------------------------------
    print("\n--- YANKI dali ve Ardo ---")
    rey = fresh(points=6, character="rey")
    ardo = fresh(points=6, character="ardo")
    check(tree.branch_usable(rey, tree.BRANCH_ECHO),
          "Rey YANKI dalini oynayabilir")
    check(not tree.branch_usable(ardo, tree.BRANCH_ECHO),
          "Ardo YANKI dalini duymuyor - ekran soluklastirabilsin")
    for key in (tree.BRANCH_BLADE, tree.BRANCH_STONE):
        check(tree.branch_usable(rey, key) and tree.branch_usable(ardo, key),
              f"{key} dali iki karakterde de anlamli")
    # `can_unlock` bilerek yalnizca puan+onkosul bakiyor: "neden alamiyorum"
    # sorusunun iki ayri cevabi olmasin.
    check(tree.can_unlock(ardo, tree.ECHO_REACH),
          "can_unlock karakter sormuyor - sozlesme puan + onkosul")

    # --- 7. Kayit: yeni alanlar ve ESKI KAYIT -------------------------------
    print("\n--- kayit ---")
    default = SaveData()
    check(default.skill_points == 0 and default.skills == [],
          "yeni kayit sifir puan, bos liste")
    other = SaveData()
    other.skills.append(tree.BLADE_EDGE)
    check(default.skills == [],
          "iki kayit ayni listeyi PAYLASMIYOR (default_factory)",
          str(default.skills))

    save = fresh(points=3)
    tree.unlock(save, tree.BLADE_EDGE)
    tree.unlock(save, tree.BLADE_FLOW)
    raw = save.to_dict()
    check("skill_points" in raw and "skills" in raw,
          "yeni alanlar diske yaziliyor")
    back = SaveData.from_dict(json.loads(json.dumps(raw)))
    check(back.skills == save.skills and back.skill_points == save.skill_points,
          "JSON gidip donuyor", f"{back.skills} / {back.skill_points}")
    check(tree.unlocked(back, tree.BLADE_EDGE)
          and tree.spent_points(back) == 2,
          "yuklenen kayitta agac ayni yerde duruyor")

    # ESKI KAYIT: bu alanlari hic bilmeyen bir dosya. Oyun bu yuzden
    # cokerse oyuncunun saatlerce ilerlemesi gider (systems/save.py).
    legacy = {
        "version": 1, "chapter": 3, "chapter_name": "chapter.torch_crypt",
        "character": "rey", "gold": 210, "max_health": 80, "health": 62,
        "abilities": ["sword", "dodge"], "charms": ["bloody_whet"],
        "weapon": "sword", "echo_tier": 2, "best_combo": 17,
    }
    old = SaveData.from_dict(legacy)
    check(old.skill_points == 0 and old.skills == [],
          "eski kayit aciliyor - yeni alanlar varsayilana dusuyor")
    check(old.gold == 210 and old.charms == ["bloody_whet"],
          "eski kaydin geri kalani bozulmadi")
    check(tree.available_points(old) == 0 and tree.spent_points(old) == 0,
          "agac eski kayitta sifirdan basliyor")
    check(not tree.can_unlock(old, tree.BLADE_EDGE),
          "puani olmayan eski kayit hicbir sey acamiyor")
    tree.grant_points(old, 1)
    check(tree.unlock(old, tree.BLADE_EDGE),
          "eski kayit puan kazaninca normal calisiyor")

    # Kaldirilmis/bilinmeyen bir dugum kayitta kalirsa oyun cokmemeli.
    ghost = SaveData.from_dict({**legacy, "skills": ["kaldirilmis_dugum"],
                                "skill_points": 2})
    check(tree.spent_points(ghost) == 0,
          "tanimadigimiz anahtarin bedeli uydurulmuyor")
    check(tree.available_points(ghost) == 2 and near(
        tree.damage_scale(ghost.skills, idle), 1.0),
        "tanimadigimiz anahtar etkileri bozmuyor")

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Yetenek agaci belgedeki kurallara uyuyor.")
    return 0


raise SystemExit(main())
