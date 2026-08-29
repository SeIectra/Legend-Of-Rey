"""Kalkanli - Katman 2'nin ilk uyesi, Bolum 5'te tek ornekle taniticiliyor.

`docs/gdd.md` 7: *"Kalkanli - onden vurulmaz, arkaya gec."*
Katman 2'nin sorusu: **combo'yu KIRMAYI ogren.**

Katman 1'in ucu de "combo KURMAYI" ogretiyordu: dur, ritmi say, zinciri
tamamla. Kalkanli bunun tersini yapiyor - onden vurmaya devam eden oyuncu
zinciri **kirilarak** cezalandiriliyor. Ders bir metinle degil, oyuncunun
kendi zincir sayacinin sifirlanmasiyla veriliyor.

## Iki gecerli cevap - bilerek iki tane

1. **Arkaya gec.** Kacinma dusmanin icinden geciyor (aktorler yalnizca
   tile'larla carpisiyor). Arkadan gelen vurus tam hasar veriyor **ve
   kesin sendeletiyor**.
2. **Saldirisini yemle, toparlanirken vur.** Kalkan yalnizca beklerken
   yukarida; TELL/ATTACK/RECOVER boyunca **inik**. `SHIELDBEARER_RECOVER_
   FRAMES` uzunlugu (38) tam olarak bu pencereyi acmak icin uzun.

Tek cevap birakmak daha "saf" olurdu ama daha kotu: oyuncunun kendi
cozumunu bulmasi, verilen cozumu uygulamasindan cok daha iyi hissettiriyor.
Ikisi de ayni dersi ogretiyor - **kalkan bir yon, ve yonler degisir.**

## Donme gecikmesi - bulmacanin tek ayar dugmesi

`Enemy._face_player()` |dx| > 2 olur olmaz aninda donuyor. Kalkanli o
davranisi **ezmek zorunda**, yoksa arkaya gecmek imkansiz olur ve dusman
cozulemez hale gelir. Bunun yerine oyuncu arkasinda kaldigi surece bir
sayac isliyor; `SHIELDBEARER_TURN_FRAMES` dolunca kisa bir parlama
(`SHIELDBEARER_TURN_TELL_FRAMES`) ve ardindan donuyor.

Donusun de okunur olmasi sart: oyuncu "arkasindayim, guvendeyim"
sanirken sessizce donerse bu haksizlik gibi gelir. Parlama sozlesme.

## Kalkan hasar vermiyor

Bloklanan vurus **sifir hasar**: ceza can degil, **ritim**. Can cezasi
olsaydi oyuncu deneme yapmaktan korkar ve dersi hic bulamazdi. Geri
itme (`SHIELDBEARER_BLOCK_PUSHBACK`) yeterli - "buradan olmuyor" bilgisi
gorsel/isitsel geliyor, hasar barindan degil.

## Goblin kanonu

`CLAUDE.md`/DEVIR: goblin ayri bir dusman olarak eklenmiyor, Kalkanli
goblin'in ruhuyla yapildi - yesil ten, sivri kulak, bicak + kalkan
(`SHIELDBEARER_SPEC`, `src/art/animation.py`).
"""
from __future__ import annotations

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import DamageResult
from src.config import (
    SHIELDBEARER_ACTIVE_FRAMES, SHIELDBEARER_BLOCK_PUSHBACK,
    SHIELDBEARER_DAMAGE, SHIELDBEARER_HEALTH, SHIELDBEARER_POISE,
    SHIELDBEARER_REACH, SHIELDBEARER_RECOVER_FRAMES, SHIELDBEARER_SPEED,
    SHIELDBEARER_TURN_FRAMES, SHIELDBEARER_TURN_TELL_FRAMES,
    TELL_FRAMES_SHIELDBEARER,
)
from src.entities.enemy import Enemy, EnemyState

# Kalkanin inik oldugu durumlar. Saldirirken ve sendelerken korunmuyor -
# oyuncunun ikinci cevabi burada yasiyor.
_UNGUARDED = (EnemyState.TELL, EnemyState.ATTACK, EnemyState.RECOVER,
              EnemyState.STAGGER, EnemyState.DEAD)


class Shieldbearer(Enemy):
    """Onden vurulmaz. Arkasi acik. Yavas doner."""

    body_width = 13
    body_height = 23
    max_health = SHIELDBEARER_HEALTH
    poise = SHIELDBEARER_POISE

    tell_frames = TELL_FRAMES_SHIELDBEARER
    active_frames = SHIELDBEARER_ACTIVE_FRAMES
    recover_frames = SHIELDBEARER_RECOVER_FRAMES
    attack_damage = SHIELDBEARER_DAMAGE
    attack_reach = SHIELDBEARER_REACH
    attack_height = 16
    attack_knockback = 1.7
    move_speed = SHIELDBEARER_SPEED
    contact_range = 22.0

    sprite_name = "shieldbearer"
    # RENK adi, zincir degil - "steel" bir SHADE CHAIN, palet rengi
    # degil. Bu tuzaga proje defalarca dustu.
    body_colour = "moss_dark"
    tell_sound = "enemy_tell"
    death_sound = "shambler_death"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        # Oyuncu kac karedir arkada. Donme gecikmesinin tamami bu sayac.
        self.behind_frames = 0
        # Donus parlamasi surerken bu sayac isliyor; bitince yon degisiyor.
        self.turn_tell_frames = 0
        # Cizim ve test icin: son karede kalkan blokladi mi.
        self.block_flash = 0

    # --- Kalkan -------------------------------------------------------------
    @property
    def guarding(self) -> bool:
        """Kalkan yukarida mi. Saldiri ve sendeleme boyunca inik."""
        return self.state not in _UNGUARDED

    def attacked_from_behind(self, box) -> bool:
        """Vurus arkadan mi geldi.

        Kutunun **sahibine** degil kutunun kendi merkezine bakiyoruz:
        oyuncu Kalkanli'nin icinden gecerken govde merkezleri neredeyse
        ust uste biniyor ve sahibin konumu guvenilmez oluyor. Hitbox ise
        daima vuran yonde aciliyor, yani gercek yonu o tasiyor.
        """
        return (box.rect.centerx - self.body.center_x) * self.facing < 0

    def take_damage(self, box, direction):
        if self.guarding and not self.attacked_from_behind(box):
            self._block(box)
            return DamageResult(hit=False, blocked=True)

        result = super().take_damage(box, direction)
        # Arkadan gelen vurus **kesin sendeletiyor**. Dogru cozumun odulu
        # "biraz daha hasar" degil, gorunur bir kirilma anı olmali - yoksa
        # oyuncu arkaya gecmenin ise yaradigini fark etmez.
        if result.hit and not result.killed and self.attacked_from_behind(box):
            if not result.staggered:
                self.poise_left = self.poise
                self.stagger_frames = self._stagger_length()
                result.staggered = True
                self._set_state(EnemyState.STAGGER)
                self.scene.tokens.force_release(self)
                self.on_attack_cancelled()
        return result

    def _block(self, box) -> None:
        """Vurus kalkana carpti: hasar yok, **zincir kirildi**."""
        self.block_flash = 8
        self.aware = True
        attacker = getattr(box, "owner", None)
        if attacker is not None and attacker is getattr(
                self.scene, "player", None):
            # Katman 2'nin dersi tam olarak burada veriliyor: zincir
            # sifirlaniyor. Metin degil, sayacin kendisi soyluyor.
            chain = getattr(attacker, "chain", None)
            if chain is not None:
                chain.cancel()
            combo = getattr(attacker, "combo", None)
            if combo is not None:
                combo.reset()
            attacker.body.vx = -self.facing * SHIELDBEARER_BLOCK_PUSHBACK

        on_blocked = getattr(self.scene, "on_shield_block", None)
        if on_blocked:
            on_blocked(self)

    # --- Donme --------------------------------------------------------------
    def _player_is_behind(self) -> bool:
        player = self.player
        if player is None:
            return False
        delta = player.body.center_x - self.body.center_x
        if abs(delta) < 4.0:
            return False        # Tam ustunde - "arka" diye bir sey yok
        return (delta * self.facing) < 0

    def _face_player(self) -> None:
        """Ani donusu **ezer**. Bkz. modul basligi.

        TELL/ATTACK sirasinda hic donmuyor: saldiri baslamissa yon
        kilitli, yoksa tell okumak anlamsizlasir.
        """
        if self.state in (EnemyState.TELL, EnemyState.ATTACK):
            return
        if self._player_is_behind():
            return                          # Donus `_update_turn` isinde
        self.behind_frames = 0
        self.turn_tell_frames = 0
        super()._face_player()

    def _update_turn(self) -> None:
        if self.turn_tell_frames > 0:
            self.turn_tell_frames -= 1
            if self.turn_tell_frames == 0:
                self.facing = -self.facing
                self.behind_frames = 0
            return

        if not self.aware or not self._player_is_behind():
            self.behind_frames = 0
            return
        if self.state in (EnemyState.TELL, EnemyState.ATTACK):
            return          # Saldiri sirasinda yon kilitli

        self.behind_frames += 1
        if self.behind_frames >= SHIELDBEARER_TURN_FRAMES:
            self.turn_tell_frames = SHIELDBEARER_TURN_TELL_FRAMES
            on_turn = getattr(self.scene, "on_shield_turn", None)
            if on_turn:
                on_turn(self)

    # --- Dongu --------------------------------------------------------------
    def _think(self) -> None:
        if self.block_flash > 0:
            self.block_flash -= 1
        self._update_turn()
        # Donus parlamasi sirasinda ayaklari cakili: oyuncu "simdi
        # donuyor" isaretini gorup karar verebilmeli.
        if self.turn_tell_frames > 0 and self.state is not EnemyState.STAGGER:
            self.body.approach_vx(0.0, 0.5)
            return
        super()._think()

    # --- Animasyon ve cizim -------------------------------------------------
    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack1")
        elif self.turn_tell_frames > 0:
            # `turn` pozu tam bu is icin zaten vardi (oyuncunun kosarken
            # yon degistirmesi icin yazilmisti, `src/art/animation.py`
            # `_turn`): once geri yaslanma, sonra pivot. Uc kare x 3 tutus
            # = 9 kare, `SHIELDBEARER_TURN_TELL_FRAMES` (10) icine tam
            # oturuyor. Yeni kare cizmedik.
            self.animator.play("turn", restart=True)
        elif abs(self.body.vx) > 0.08:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    def update(self) -> None:
        super().update()
        self._update_animation()

    def draw(self, surface, offset) -> None:
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)

    def tell_colour(self):
        """Donus parlamasi da tell rengini kullaniyor.

        Ayri bir renk daha eklemek renk korlugu icin ek yuk olurdu; siluet
        farki zaten var (donus sirasinda duruyor, saldiri tell'inde
        kabariyor).
        """
        from src.art import palette
        if self.turn_tell_frames > 0:
            return palette.color("danger_bright")
        return super().tell_colour()

    @property
    def telegraphing(self) -> bool:
        return super().telegraphing or self.turn_tell_frames > 0

    def silhouette_scale(self) -> tuple[float, float]:
        if self.block_flash > 0:
            # Bloklarken cokuyor - "durdurdum" hissi. Tell'in tersi yonde
            # deformasyon, yani ikisi bir bakista ayrilabiliyor.
            return (1.14, 0.90)
        return super().silhouette_scale()
