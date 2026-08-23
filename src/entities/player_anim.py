"""Oyuncu animasyon durumu - oynanistan turer, tersi degil.

**Saldirilar ilerlemeyle surulur.** Kare, saldirinin kendi kare
butcesindeki konumdan seciliyor; boylece animasyon dovus zamanlamasini asla
kaydiramaz. Ters kurulsaydi (animasyon karesi hitbox'i acsaydi) bir sanat
degisikligi sessizce combo penceresini bozardi.

`player.py`'den ayrildi: dosya 400 satiri asmisti (CLAUDE.md 11) ve bu blok
zaten ayri bir sorumluluk - **hangi animasyon**, **hangi karede**.
"""
from __future__ import annotations

from src.art.animation import ANIMATIONS, CHARACTERS
from src.art.spritegen import weapon_tip
from src.combat.combo import AttackPhase
from src.config import DODGE_TOTAL_FRAMES


def update_animation(player) -> None:
    """Animasyon durumu oynanistan turer, tersi degil.

    Saldirilar **ilerlemeyle** surulur: kare, saldirinin kendi kare
    butcesindeki konumdan secilir. Boylece animasyon dovus zamanlamasini
    asla kaydiramaz.
    """
    if player.dead:
        player.animator.play("death")
        player.animator.update()
        return

    if player.chain.busy:
        state = f"attack{min(player.chain.index + 1, 3)}"
        player.animator.play(state)
        progress = attack_progress(player)
        player.animator.set_progress(progress)
        _feed_trail(player, state, progress)
        return
    player.trail.clear()

    if player.hurt_frames > 0:
        player.animator.play("hurt")
    elif player.dodge.active:
        player.animator.play("dodge")
        player.animator.set_progress(
            1.0 - player.dodge.frames_left / max(1, DODGE_TOTAL_FRAMES))
        return
    elif not player.body.grounded:
        player.animator.play("jump" if player.body.vy < -0.3 else "fall")
    elif abs(player.body.vx) > 0.25:
        player.animator.play("run")
    else:
        player.animator.play("idle")
    player.animator.update()

def attack_progress(player) -> float:
    """Su anki saldirinin 0..1 arasi ilerlemesi."""
    spec = player.chain.spec
    total = spec.total
    if total <= 0:
        return 1.0
    if player.chain.phase is AttackPhase.WINDUP:
        done = spec.windup - player.chain.phase_frames_left
    elif player.chain.phase is AttackPhase.ACTIVE:
        done = spec.windup + (spec.active - player.chain.phase_frames_left)
    else:
        done = (spec.windup + spec.active
                + (spec.recovery - player.chain.phase_frames_left))
    return max(0.0, min(1.0, done / total))

# --- Hareket ------------------------------------------------------------


def _feed_trail(player, state: str, progress: float) -> None:
    """Silahin ucunu izin uzerine ekler (src/art/trail.py).

    Uc, sprite'i cizen **ayni** poz fonksiyonundan hesaplaniyor
    (`spritegen.weapon_tip`) - yaklasik bir noktadan degil. Poz degisirse
    iz de kendiliginden dogru kalir.

    Hucre -> dunya donusumu `player_render.draw_player` ile ayni:
    yatayda merkez, dikeyde sprite'in TABAN CIZGISI govdenin altina
    hizali. Sola bakarken sprite aynalandigi icin `tip_x` de aynalanmali;
    unutulursa iz karakterin arkasindan cikar.
    """
    spec = CHARACTERS.get(player.animator.character)
    if spec is None:
        return
    pose_fn, count, looping = ANIMATIONS.get(state, (None, 1, False))
    if pose_fn is None:
        return
    tip = weapon_tip(spec, pose_fn(max(0.0, min(1.0, progress))))
    if tip is None:
        return                      # Silahsiz (yumruk) - iz yok
    # Bitirici izi ALTIN, normal vurus celik beyazi. Zincirin ucuncu
    # vurusu docs/dovus-sistemi.md'de ayri bir agirliga sahip (7 kare
    # hitstop, iptal edilemez) - o agirlik gorsel olarak da okunmali.
    player.trail.chain = "brass" if player.chain.is_finisher else "bone_pale"
    tip_x, tip_y = tip
    if player.facing < 0:
        tip_x = spec.cell_width - tip_x
    world_x = player.body.center_x - spec.cell_width * 0.5 + tip_x
    world_y = player.body.bottom - player.sprite_foot_y + tip_y
    player.trail.add(world_x, world_y)
