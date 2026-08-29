"""Yetenek agaci - uc dal, dort seviye.

`docs/gdd.md` 6: *"Yetenek agaci (3 dal x 4 seviye)"*. `docs/yapi.md` B4:
ilk agac ekrani **Kayit Odasi**'nda aciliyor - dovussuz bir nefes bolumu.

Bu dosya agacin **mantigi**: ne var, neyin onkosulu ne, kim neyi alabilir,
ve acilanlarin toplam etkisi ne. Cizim `src/ui/skill_tree.py`'de; modul
durumsuz, durum kayitta (`SaveData.skills` + `SaveData.skill_points`).
Ayni ayrim `charms.py` ve `abilities.py`'de de var.

## Agac neden tamamlanamiyor

`docs/ekonomi-uretim.md` 1 oyun boyunca kabaca **6 yetenek puani** veriyor.
Agacin tamami 18 puan eder. Yani oyuncu asla hepsini alamaz: ya bir dali
dibine kadar acar (1+1+2+2 = 6), ya uc dalin ilk iki seviyesini. Ekipmanda
oldugu gibi burada da kural ayni - *"her bolumde bir sey alabilmeli, ama
her seyi alamamali"*.

Bu yuzden bedeller **artan**: ust seviyeler ucuz olsaydi oyuncu uc dali da
yariya kadar acar ve hicbir sey secmemis olurdu.

## Onkosul zinciri

Bir dugum ancak **ustundeki seviye acikken** alinabilir. Seviye atlanamaz.
Onkosul olmasaydi oyuncu uc dalin en guclu dugumunu toplar ve dallarin
karakteri diye bir sey kalmazdi.

## Etkiler carpan/bonus - taban degerlere DOKUNULMAZ

`docs/dovus-sistemi.md`'deki kare degerleri baglayici (CLAUDE.md 7).
Yetenekler onlarin **ustune** biner: zincir penceresi 12/14/10 oldugu gibi
kalir, KESKIN dalinin "Akis" dugumu uzerine +2 kare ekler. Hicbir yetenek
bir taban sayiyi yeniden yazmiyor.

Toplayicilar `charms.py` desenini birebir izliyor: carpanlar **carpilarak**
birlesir (dogal azalan getiri), duz bonuslar toplanarak.

## Yanki dali ve Ardo

Ardo Yanki'yi duymuyor - bu bir eksiklik degil karakter farki (DEVIR.md
3.7). YANKI dalinin etkileri onda sessizce notr kalir. Dali gizlemek ya da
soluklastirmak icin ekran `branch_usable(save, "echo")` sorar; `can_unlock`
bilerek yalnizca **puan ve onkosul** bakiyor (sozlesme bu), yoksa "neden
alamiyorum" sorusunun iki ayri cevabi olurdu.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Iterable

from src.config import (
    COMBO_THRESHOLD_MID, SKILL_BRANCH_LEVELS, SKILL_COST_BY_LEVEL,
    SKILL_EDGE_DAMAGE_BONUS, SKILL_FINISHER_DAMAGE_BONUS,
    SKILL_FLOW_CHAIN_FRAMES, SKILL_GRIP_SIGHT_BONUS,
    SKILL_GUARD_DEFENCE_RELIEF, SKILL_HIDE_HEALTH_BONUS,
    SKILL_MEND_COMBO_RELIEF, SKILL_MOMENTUM_DAMAGE_BONUS,
    SKILL_REACH_SIGHT_BONUS, SKILL_ROLL_DODGE_CHARGES,
    SKILL_WARD_DEFENCE_RELIEF, SKILL_WILL_DEFENCE_RELIEF,
    SKILL_WILL_HEALTH_BONUS,
)
from src.entities.character_stats import ARDO, REY

if TYPE_CHECKING:                      # yalnizca tip icin - dongusel import yok
    from src.systems.save import SaveData


# --- Dugum anahtarlari ------------------------------------------------------
# Kayit dosyasina **bu dizeler** yaziliyor (abilities.py ve charms.py ile
# ayni kural): yeni dugum eklemek serbest, var olani yeniden adlandirmak
# eski kayitlarin yeteneklerini yok eder.
BLADE_EDGE = "blade_edge"
BLADE_FLOW = "blade_flow"
BLADE_MOMENTUM = "blade_momentum"
BLADE_FINISHER = "blade_finisher"

ECHO_REACH = "echo_reach"
ECHO_WARD = "echo_ward"
ECHO_GRIP = "echo_grip"
ECHO_MEND = "echo_mend"

STONE_HIDE = "stone_hide"
STONE_GUARD = "stone_guard"
STONE_ROLL = "stone_roll"
STONE_WILL = "stone_will"

BRANCH_BLADE = "blade"
BRANCH_ECHO = "echo"
BRANCH_STONE = "stone"


def _neutral(player: object) -> float:
    """Carpan kanallarinin varsayilani. Hicbir sey yapmaz."""
    return 1.0


@dataclass(frozen=True)
class Node:
    """Agactaki tek bir dugum.

    `label_key` / `desc_key` dil anahtari tutar, hazir metin degil - kayit
    ve arayuz dilden bagimsiz kalsin (charms.py ile ayni kural).

    Carpan alanlari oyuncunun **o andaki** durumuna bakar: "10+ combo'da
    hasar" gibi kosullu bir yetenek her karede yeniden karar verir. Duz
    bonus alanlari duruma bakmaz - acildigi anda sabittir.
    """

    key: str
    label_key: str
    desc_key: str
    cost: int

    # Carpan kanallari (durumsal)
    damage_scale: Callable[[object], float] = _neutral
    defence_scale: Callable[[object], float] = _neutral      # ALINAN hasar
    echo_sight_scale: Callable[[object], float] = _neutral

    # Duz bonuslar (sabit) - hepsi baglayici taban degerin USTUNE eklenir
    max_health: int = 0
    chain_window: int = 0        # kare
    dodge_charges: int = 0
    restore_combo: int = 0       # COMBO_TO_RESTORE'dan dusulecek vurus sayisi


@dataclass(frozen=True)
class Branch:
    """Bir dal: dort seviye, yukaridan asagi sirali."""

    key: str
    label_key: str
    desc_key: str
    nodes: tuple[Node, ...]
    # Yalniz Yanki tasiyan karakterde ise yarar (Rey). Ekran bunu
    # soluklastirmak icin `branch_usable()` sorar.
    requires_echo: bool = False


# --- Kosullu etkiler --------------------------------------------------------
# Hepsi `charms.py`'deki desenle ayni: oyuncudan `getattr` ile okur, eksik
# alanda notr doner. Test cift yonlu (kosul saglaninca / saglanmayinca)
# dogruluyor.
def _edge_damage(player: object) -> float:
    """Kosulsuz keskinlik. Dalin girisi - her oynayis bicimine calisir."""
    return 1.0 + SKILL_EDGE_DAMAGE_BONUS


def _momentum_damage(player: object) -> float:
    """10+ combo'da hasar. Saldirgan oynayani odullendirir, cekingeni degil."""
    combo = getattr(player, "combo", None)
    count = getattr(combo, "count", 0)
    return (1.0 + SKILL_MOMENTUM_DAMAGE_BONUS if count >= COMBO_THRESHOLD_MID
            else 1.0)


def _finisher_damage(player: object) -> float:
    """Yalniz zincirin son vurusunda. Bitiriciyi savurmak zaten bir karar."""
    chain = getattr(player, "chain", None)
    if chain is None or not getattr(chain, "busy", False):
        return 1.0
    if not getattr(chain, "is_finisher", False):
        return 1.0
    return 1.0 + SKILL_FINISHER_DAMAGE_BONUS


def _has_echo(player: object) -> bool:
    """Sahnedeki Yanki durumu. Ardo'da `scene.echo` None (scenes/play.py)."""
    return getattr(getattr(player, "scene", None), "echo", None) is not None


def _reach_sight(player: object) -> float:
    return 1.0 + SKILL_REACH_SIGHT_BONUS if _has_echo(player) else 1.0


def _grip_sight(player: object) -> float:
    return 1.0 + SKILL_GRIP_SIGHT_BONUS if _has_echo(player) else 1.0


def _ward_defence(player: object) -> float:
    """Yanki ACIKKEN alinan hasari azaltir - bedeli hafifletir, silmez.

    Sifirlasaydi mekanigin kalbi olurdu: Yanki'nin yardimi bedelsiz kalinca
    "acik tut, unut" haline gelirdi (systems/echo.py "Bedel").
    """
    echo = getattr(getattr(player, "scene", None), "echo", None)
    if echo is None or not getattr(echo, "active", False):
        return 1.0
    return 1.0 - SKILL_WARD_DEFENCE_RELIEF


def _guard_defence(player: object) -> float:
    return 1.0 - SKILL_GUARD_DEFENCE_RELIEF


def _will_defence(player: object) -> float:
    return 1.0 - SKILL_WILL_DEFENCE_RELIEF


# --- Agac -------------------------------------------------------------------
# Dil anahtarlari **acikca** yazili: f-string ile kurulan anahtari
# tests/test_lang.py kaynak taramasinda goremiyor ve "olu anahtar" sayiyor.
BRANCHES: tuple[Branch, ...] = (
    Branch(
        key=BRANCH_BLADE,
        label_key="skill.blade",
        desc_key="skill.blade_desc",
        nodes=(
            Node(key=BLADE_EDGE,
                 label_key="skill.blade_edge",
                 desc_key="skill.blade_edge_desc",
                 cost=SKILL_COST_BY_LEVEL[0],
                 damage_scale=_edge_damage),
            Node(key=BLADE_FLOW,
                 label_key="skill.blade_flow",
                 desc_key="skill.blade_flow_desc",
                 cost=SKILL_COST_BY_LEVEL[1],
                 chain_window=SKILL_FLOW_CHAIN_FRAMES),
            Node(key=BLADE_MOMENTUM,
                 label_key="skill.blade_momentum",
                 desc_key="skill.blade_momentum_desc",
                 cost=SKILL_COST_BY_LEVEL[2],
                 damage_scale=_momentum_damage),
            Node(key=BLADE_FINISHER,
                 label_key="skill.blade_finisher",
                 desc_key="skill.blade_finisher_desc",
                 cost=SKILL_COST_BY_LEVEL[3],
                 damage_scale=_finisher_damage),
        ),
    ),
    Branch(
        key=BRANCH_ECHO,
        label_key="skill.echo",
        desc_key="skill.echo_desc",
        requires_echo=True,
        nodes=(
            Node(key=ECHO_REACH,
                 label_key="skill.echo_reach",
                 desc_key="skill.echo_reach_desc",
                 cost=SKILL_COST_BY_LEVEL[0],
                 echo_sight_scale=_reach_sight),
            Node(key=ECHO_WARD,
                 label_key="skill.echo_ward",
                 desc_key="skill.echo_ward_desc",
                 cost=SKILL_COST_BY_LEVEL[1],
                 defence_scale=_ward_defence),
            Node(key=ECHO_GRIP,
                 label_key="skill.echo_grip",
                 desc_key="skill.echo_grip_desc",
                 cost=SKILL_COST_BY_LEVEL[2],
                 echo_sight_scale=_grip_sight),
            Node(key=ECHO_MEND,
                 label_key="skill.echo_mend",
                 desc_key="skill.echo_mend_desc",
                 cost=SKILL_COST_BY_LEVEL[3],
                 restore_combo=SKILL_MEND_COMBO_RELIEF),
        ),
    ),
    Branch(
        key=BRANCH_STONE,
        label_key="skill.stone",
        desc_key="skill.stone_desc",
        nodes=(
            Node(key=STONE_HIDE,
                 label_key="skill.stone_hide",
                 desc_key="skill.stone_hide_desc",
                 cost=SKILL_COST_BY_LEVEL[0],
                 max_health=SKILL_HIDE_HEALTH_BONUS),
            Node(key=STONE_GUARD,
                 label_key="skill.stone_guard",
                 desc_key="skill.stone_guard_desc",
                 cost=SKILL_COST_BY_LEVEL[1],
                 defence_scale=_guard_defence),
            Node(key=STONE_ROLL,
                 label_key="skill.stone_roll",
                 desc_key="skill.stone_roll_desc",
                 cost=SKILL_COST_BY_LEVEL[2],
                 dodge_charges=SKILL_ROLL_DODGE_CHARGES),
            Node(key=STONE_WILL,
                 label_key="skill.stone_will",
                 desc_key="skill.stone_will_desc",
                 cost=SKILL_COST_BY_LEVEL[3],
                 max_health=SKILL_WILL_HEALTH_BONUS,
                 defence_scale=_will_defence),
        ),
    ),
)

# Duz aramalar - agac sabit oldugu icin bir kez kuruluyor.
NODES: dict[str, Node] = {
    node.key: node for branch in BRANCHES for node in branch.nodes
}
_BRANCH_OF: dict[str, Branch] = {
    node.key: branch for branch in BRANCHES for node in branch.nodes
}
_LEVEL_OF: dict[str, int] = {
    node.key: level
    for branch in BRANCHES
    for level, node in enumerate(branch.nodes, start=1)
}

# Agacin tamamini acmanin bedeli. Oyunun verdigi ~6 puanla kiyaslanabilsin
# diye adlandirildi - denge tartismasi sayiyi tahmin ederek yapilmasin.
TOTAL_COST: int = sum(node.cost for node in NODES.values())


# --- Sorgular ---------------------------------------------------------------
def get(node_key: str) -> Node | None:
    return NODES.get(node_key)


def branch_of(node_key: str) -> Branch | None:
    return _BRANCH_OF.get(node_key)


def level_of(node_key: str) -> int:
    """Dugumun dalindaki seviyesi (1..4). Bilinmeyen dugum 0."""
    return _LEVEL_OF.get(node_key, 0)


def label_key(node_key: str) -> str:
    node = NODES.get(node_key)
    return node.label_key if node else "skill.unknown"


def desc_key(node_key: str) -> str:
    node = NODES.get(node_key)
    return node.desc_key if node else "skill.unknown"


def prerequisite(node_key: str) -> Node | None:
    """Bir ust seviyedeki dugum. Ilk seviyede None."""
    branch = _BRANCH_OF.get(node_key)
    level = _LEVEL_OF.get(node_key, 0)
    if branch is None or level <= 1:
        return None
    return branch.nodes[level - 2]


def branch_usable(save: "SaveData", branch_key: str) -> bool:
    """Bu kayittaki karakter icin dalin bir anlami var mi?

    Yalnizca **arayuz** icin: Ardo'ya YANKI dalini soluk gostermek icin.
    `can_unlock` bunu bilerek sormuyor - bkz. dosya basi.
    """
    branch = next((b for b in BRANCHES if b.key == branch_key), None)
    if branch is None:
        return False
    if not branch.requires_echo:
        return True
    stats = ARDO if getattr(save, "character", "rey") == "ardo" else REY
    return stats.has_echo


# --- Puan muhasebesi --------------------------------------------------------
def unlocked(save: "SaveData", node_key: str) -> bool:
    return node_key in (getattr(save, "skills", None) or ())


def spent_points(save: "SaveData") -> int:
    """Acilmis dugumlere yatirilan toplam puan.

    Kayitta tanimadigimiz bir anahtar varsa (eski surumden kalma, ya da
    kaldirilmis bir dugum) sayilmaz - bilmedigimiz bir seyin bedelini
    uydurmaktansa gormezden gelmek dogru.
    """
    total = 0
    for key in (getattr(save, "skills", None) or ()):
        node = NODES.get(key)
        if node is not None:
            total += node.cost
    return total


def available_points(save: "SaveData") -> int:
    """Harcanabilir puan. `skill_points` **kalan** havuzdur, kazanilan degil."""
    return max(0, int(getattr(save, "skill_points", 0) or 0))


def grant_points(save: "SaveData", count: int = 1) -> int:
    """Puan ekler (nefes bolumu odulu, tuccar, bulmaca). Yeni toplami doner."""
    save.skill_points = available_points(save) + max(0, count)
    return save.skill_points


def can_unlock(save: "SaveData", node_key: str) -> bool:
    """Puan yeter mi VE bir ustteki seviye acik mi?

    Seviye atlanamaz: yoksa oyuncu uc dalin en guclu dugumunu toplar ve
    dallarin karakteri diye bir sey kalmaz.
    """
    node = NODES.get(node_key)
    if node is None or unlocked(save, node_key):
        return False
    if available_points(save) < node.cost:
        return False
    previous = prerequisite(node_key)
    if previous is not None and not unlocked(save, previous.key):
        return False
    return True


def unlock(save: "SaveData", node_key: str) -> bool:
    """Dugumu acar ve puani duser. Acilamazsa hicbir sey degistirmeden False.

    Kismi degisiklik birakmiyor: once kosul, sonra iki yazma. Puan dusup
    dugum eklenmeseydi oyuncu sessizce puan kaybederdi.
    """
    if not can_unlock(save, node_key):
        return False
    node = NODES[node_key]
    if getattr(save, "skills", None) is None:
        save.skills = []
    save.skill_points = available_points(save) - node.cost
    save.skills.append(node_key)
    return True


def unlocked_nodes(save: "SaveData") -> tuple[Node, ...]:
    """Acilmis dugumler, agactaki siralariyla (kayit sirasiyla degil)."""
    return tuple(node for node in NODES.values() if unlocked(save, node.key))


# --- Etki toplayicilari -----------------------------------------------------
# `charms.py` ile ayni desen ve ayni gerekce: carpanlar **carpilarak**
# birlesir. Toplama secilseydi yetenek sayisi artinca etki dogrusal
# patlardi; carpma dogal bir azalan getiri sagliyor.
def damage_scale(keys: Iterable[str], player: object) -> float:
    """Acik yeteneklerin **verilen** hasar carpani."""
    total = 1.0
    for key in keys:
        node = NODES.get(key)
        if node is not None:
            total *= node.damage_scale(player)
    return total


def defence_scale(keys: Iterable[str], player: object) -> float:
    """Acik yeteneklerin **alinan** hasar carpani. 1.0'in altinda = koruma."""
    total = 1.0
    for key in keys:
        node = NODES.get(key)
        if node is not None:
            total *= node.defence_scale(player)
    return total


def echo_sight_scale(keys: Iterable[str], player: object) -> float:
    """Yanki gorus menzili carpani (systems/echo.py `sight_range`)."""
    total = 1.0
    for key in keys:
        node = NODES.get(key)
        if node is not None:
            total *= node.echo_sight_scale(player)
    return total


def _flat(keys: Iterable[str], field_name: str) -> int:
    """Duz bonuslar toplanir - carpanlarin aksine durumdan bagimsiz."""
    total = 0
    for key in keys:
        node = NODES.get(key)
        if node is not None:
            total += getattr(node, field_name)
    return total


def max_health_bonus(keys: Iterable[str]) -> int:
    """REY_MAX_HEALTH / ARDO_MAX_HEALTH uzerine EKLENIR."""
    return _flat(keys, "max_health")


def chain_window_bonus(keys: Iterable[str]) -> int:
    """Zincir penceresine eklenen kare. Taban (14/10) degismez."""
    return _flat(keys, "chain_window")


def dodge_charge_bonus(keys: Iterable[str]) -> int:
    """Kacinma sarji. 6/18 karelik baglayici zamanlama degismez."""
    return _flat(keys, "dodge_charges")


def restore_combo_reduction(keys: Iterable[str]) -> int:
    """COMBO_TO_RESTORE'dan dusulecek vurus sayisi (20 -> 14)."""
    return _flat(keys, "restore_combo")
