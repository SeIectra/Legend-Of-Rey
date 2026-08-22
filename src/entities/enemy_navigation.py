"""Dusman dikey erisilebilirlik ve kenar-kacisi - "yapisik dusman" onleme.

`enemy.py`'nin durum makinesinden ayri dosyada (CLAUDE.md 11: dosya basina
tek sorumluluk - state machine buyudukce bu bolum onu 400 satiri asirdi).
Bu modul yalnizca tek soruya bakiyor: dusman oyuncuya dikeyde ulasabiliyor
mu, ulasamiyorsa en yakin kenardan nasil iner. Serbest fonksiyonlar
`enemy_render.py`'deki `draw_enemy(enemy, ...)` deseniyle ayni - ilk
parametre `enemy`, method degil; boylece `Enemy` sinifina geri donup
circular import acmiyor.
"""
from __future__ import annotations

from src.config import (
    ENEMY_APPROACH_SPEED, ENEMY_LEDGE_PROBE_TILES,
    ENEMY_UNREACHABLE_PATIENCE_FRAMES, ENEMY_VERTICAL_ENGAGE_RANGE, TILE_SIZE,
)


def update_reachability(enemy) -> None:
    """Oyuncuya dikeyde ulasilabilirlik - farkindalik/saldiri hakkindan
    **bagimsiz** her karede olculur.

    Once bu sayac yalnizca `_approach()` icinde artiyordu - yani dusman
    zaten APPROACH durumuna girmisse (`aware` VE saldiri hakki varsa)
    calisiyordu. Oyuncuyu hic gormemis (`aware` hic olmamis) ya da hakki hic
    alamamis (2 dusman hakki baskalarinda) bir dusman bu sayaci hicbir zaman
    baslatamiyordu ve kopuk bir platformda/tavanda sonsuza dek kalabiliyordu
    - Arda'nin bildirdigi "hala yukarida" hatasi. `Climber.aware_frames`'teki
    ayni sinif hatanin (bkz. climber.py) IDLE/ORBIT durumundaki genel dusman
    karsiligi.
    """
    player = enemy.player
    if player is None or player.dead:
        enemy._unreachable_frames = 0
        return
    if vertically_reachable(enemy, player):
        enemy._unreachable_frames = 0
    else:
        enemy._unreachable_frames += 1


def vertically_reachable(enemy, player) -> bool:
    """Oyuncu saldiri menzilinde erisilebilecek yukseklikte mi?

    `distance_to()` yalnizca yatay olcuyor - bir dusman kopuk bir platforma
    (guclu bir knockback_up ile, ya da bolum tasarimindaki bir yukseltiye)
    cikinca, oyuncu tam altindaysa yatay mesafe hep kucuk kaliyordu ve
    dusman hicbir zaman ulasamayacagi bir hedefe sonsuza dek saldiri
    **denemesi** yapiyordu - "ust platformlara sikisma" raporunun kaynagi
    buydu. Saldiriyi baslatmadan once bu da soruluyor; goruş/kusatma
    davranisi bilerek degismiyor.
    """
    return abs(enemy.body.center_y - player.body.center_y) \
        <= ENEMY_VERTICAL_ENGAGE_RANGE


def try_escape_unreachable(enemy) -> bool:
    """Sikisma kacisi - farkindalik/saldiri hakkindan **once** gelir.

    Oyuncuyu hic gormemis ya da hakki hic alamamis bir dusman bile bu esigi
    asinca kenar arar; yoksa `_think()`'teki `not aware`/`ORBIT` dallari onu
    sonsuza dek yerinde tutabilirdi. Kenar bulunup harekete gecilirse `True`
    doner - cagiran `_think()` o karede baska bir sey yapmadan cikar.
    """
    if enemy._unreachable_frames < ENEMY_UNREACHABLE_PATIENCE_FRAMES:
        return False
    # `nearest_ledge_direction()` once `enemy.facing` yonunu dener (oyuncuya
    # daha yakin kenar genelde o taraftadir). Bu yol `_approach()`'un
    # DISINDA calistigi icin (hic farkina varmamis bir dusman icin de
    # tetiklenebilsin diye) facing bu karede henuz guncellenmemis olabilir -
    # once yuzu oyuncuya cevir.
    enemy._face_player()
    edge = nearest_ledge_direction(enemy)
    if edge is None:
        return False
    # Yerel import: `EnemyState` `enemy.py`'de tanimli, o da bu modulu
    # import ediyor (`_try_escape_unreachable` wrapper'i icin) - modul
    # seviyesinde geri-import circular olurdu. Bu fonksiyon yalnizca
    # calisma zamaninda cagrildigi icin (yukleme aninda degil) guvenli.
    from src.entities.enemy import EnemyState
    enemy.facing = edge
    speed = enemy.move_speed * enemy.speed_scale * ENEMY_APPROACH_SPEED / 0.5
    enemy.body.approach_vx(edge * speed, 0.25)
    enemy._set_state(EnemyState.APPROACH)
    return True


def nearest_ledge_direction(enemy) -> int | None:
    """Zemin `ENEMY_LEDGE_PROBE_TILES` ileride kesiliyorsa o yonu doner.

    Once yuzun donuk oldugu yon denenir (oyuncuya daha yakin bir kenar
    genelde o taraftadir), sonra tersi. Ikisi de kesilmiyorsa (genis, duz
    bir platform) `None` doner - cagiran mevcut davranisi surdurur.
    """
    tilemap = getattr(enemy.scene, "tilemap", None)
    if tilemap is None:
        return None
    foot_tx = int(enemy.body.center_x) // TILE_SIZE
    foot_ty = int(enemy.body.feet[1]) // TILE_SIZE
    for direction in (enemy.facing, -enemy.facing):
        probe_tx = foot_tx + direction * ENEMY_LEDGE_PROBE_TILES
        if not (tilemap.is_solid(probe_tx, foot_ty)
                or tilemap.is_platform(probe_tx, foot_ty)):
            return direction
    return None
