"""Oyuncu animasyon durumu - oynanistan turer, tersi degil.

**Saldirilar ilerlemeyle surulur.** Kare, saldirinin kendi kare
butcesindeki konumdan seciliyor; boylece animasyon dovus zamanlamasini asla
kaydiramaz. Ters kurulsaydi (animasyon karesi hitbox'i acsaydi) bir sanat
degisikligi sessizce combo penceresini bozardi.

`player.py`'den ayrildi: dosya 400 satiri asmisti (CLAUDE.md 11) ve bu blok
zaten ayri bir sorumluluk - **hangi animasyon**, **hangi karede**.
"""
from __future__ import annotations

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
        player.animator.set_progress(attack_progress(player))
        return

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
