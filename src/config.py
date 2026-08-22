"""Tum sayisal degerler. Sihirli sayi yasak - her sey burada adlandirilir.

**Zaman birimi karedir, saniye degil.** Oyun sabit 60 FPS'te calisir; dovus
kare hassasiyeti gerektirdigi icin `dt` tabanli hesap yapilmaz. Hiz birimleri
piksel/kare, ivme piksel/kare^2.

Kaynak: `docs/dovus-sistemi.md`. Oradaki degerler **baglayicidir** - sessizce
degistirilmez. Denge sorunu gorulurse once konusulur (CLAUDE.md 7).

Belgede yer almayan degerler (platform fizigi, kamera) `# ayarlanabilir`
notuyla isaretli; bunlar deneyle bulundu ve serbestce oynatilabilir.
"""
from __future__ import annotations

from typing import Final

# =============================================================================
# EKRAN VE ZAMAN
# =============================================================================
FPS: Final[int] = 60
INTERNAL_WIDTH: Final[int] = 480
INTERNAL_HEIGHT: Final[int] = 270
TILE_SIZE: Final[int] = 16
CHARACTER_SIZE: Final[int] = 32

# Bir karede yakalanabilecek azami tick - lag sonrasi "olum sarmali" onlenir.
MAX_CATCHUP_FRAMES: Final[int] = 5

# Ekran disini cizmemek icin kamera alanina eklenen marj (tile).
TILE_DRAW_MARGIN: Final[int] = 2

# Ayni anda ekranda azami parcacik (docs/derinlestirme.md 8.4).
MAX_PARTICLES: Final[int] = 200


# =============================================================================
# OYUNCU AFFI  (docs/dovus-sistemi.md 7 - oyuncuya asla soylenmez)
# =============================================================================
COYOTE_FRAMES: Final[int] = 6           # Platformdan dustukten sonra zipla hakki
INPUT_BUFFER_FRAMES: Final[int] = 8     # Tus erken basilirsa hafizada tutulur
LAST_CHANCE_HEALTH_RATIO: Final[float] = 0.15   # Bu oranin altinda 1 canla kal
LAST_CHANCE_PER_LEVEL: Final[int] = 1
DODGE_GENEROSITY_FRAMES: Final[int] = 2  # Dokunulmazlik gorselden once baslar


# =============================================================================
# PLATFORM FIZIGI   # ayarlanabilir - dovus belgesinde yok, deneyle bulundu
# =============================================================================
GRAVITY: Final[float] = 0.22            # piksel / kare^2
MAX_FALL_SPEED: Final[float] = 7.0      # piksel / kare
TERMINAL_FALL_SPEED: Final[float] = 9.5

PLAYER_RUN_SPEED: Final[float] = 2.0    # piksel / kare  (~120 px/sn)
PLAYER_GROUND_ACCEL: Final[float] = 0.25
PLAYER_AIR_ACCEL: Final[float] = 0.17
PLAYER_GROUND_FRICTION: Final[float] = 0.32
PLAYER_AIR_FRICTION: Final[float] = 0.07

PLAYER_JUMP_SPEED: Final[float] = 5.2   # ~61 piksel yukseklik = 3.8 tile
JUMP_CUT_MULTIPLIER: Final[float] = 0.42    # Tus birakilinca yukari hiz kirpilir
APEX_SPEED_THRESHOLD: Final[float] = 0.7    # Bu hizin altinda yercekimi azalir
APEX_GRAVITY_SCALE: Final[float] = 0.62

# Bolum tasariminin ziplama zarfi - tools/measure_jump.py ile olculur.
MAX_JUMP_GAP_TILES: Final[int] = 4      # Azami ucurum genisligi
MAX_JUMP_HEIGHT_TILES: Final[int] = 3   # Basilabilir satirlar arasi azami adim


# =============================================================================
# DOVUS - ZINCIR   (docs/dovus-sistemi.md 1 - BAGLAYICI)
# =============================================================================
class ChainHit:
    """Zincirdeki tek bir vurusun kare degerleri."""

    __slots__ = ("windup", "active", "recovery", "damage", "knockback",
                 "cancelable", "hitstop")

    def __init__(self, windup: int, active: int, recovery: int, damage: int,
                 knockback: float, cancelable: bool, hitstop: int) -> None:
        self.windup = windup
        self.active = active
        self.recovery = recovery
        self.damage = damage
        self.knockback = knockback
        self.cancelable = cancelable
        self.hitstop = hitstop

    @property
    def total(self) -> int:
        return self.windup + self.active + self.recovery


# Vurus 1 ve 2'nin recovery'si kacinma ile iptal edilebilir.
# Vurus 3'un recovery'si iptal EDILEMEZ - bitiriciyi savurmak bir karardir.
CHAIN: Final[tuple[ChainHit, ...]] = (
    ChainHit(windup=4, active=3, recovery=8,  damage=10, knockback=1.6,
             cancelable=True,  hitstop=3),
    ChainHit(windup=5, active=3, recovery=9,  damage=12, knockback=1.8,
             cancelable=True,  hitstop=3),
    ChainHit(windup=8, active=5, recovery=16, damage=25, knockback=4.2,
             cancelable=False, hitstop=7),
)

CHAIN_WINDOW_FRAMES: Final[int] = 12    # Aktif kare bitince zinciri surdurme suresi


# =============================================================================
# DOVUS - KACINMA   (docs/dovus-sistemi.md 3 - BAGLAYICI)
# =============================================================================
DODGE_IFRAMES: Final[int] = 6
DODGE_TOTAL_FRAMES: Final[int] = 18
DODGE_COOLDOWN_FRAMES: Final[int] = 24
DODGE_SPEED: Final[float] = 4.2         # piksel / kare  # ayarlanabilir

COUNTER_WINDOW_FRAMES: Final[int] = 9   # Kacinmadan sonra karsi vurus penceresi
COUNTER_DAMAGE_BONUS: Final[float] = 0.30       # Rey
COUNTER_DAMAGE_BONUS_ARDO: Final[float] = 0.60  # Ardo - Yanki'sizligin telafisi


# =============================================================================
# DOVUS - HAVAYA KALDIRMA   (docs/dovus-sistemi.md 2)
# =============================================================================
JUGGLE_MAX_HITS: Final[int] = 3         # Havada yenebilecek azami vurus
JUGGLE_DAMAGE_BONUS: Final[float] = 0.20
JUGGLE_LIFT_SPEED: Final[float] = 3.4   # piksel / kare
JUGGLE_FALL_INCREMENT: Final[float] = 0.06   # Her vuruşta dusme hizi artar


# =============================================================================
# COMBO SAYACI   (docs/dovus-sistemi.md 4 - BAGLAYICI)
# =============================================================================
COMBO_RESET_FRAMES: Final[int] = 90     # 1.5 saniye sessizlikte sifirlanir

COMBO_THRESHOLD_LOW: Final[int] = 5
COMBO_THRESHOLD_MID: Final[int] = 10
COMBO_THRESHOLD_HIGH: Final[int] = 20

COMBO_GOLD_MULTIPLIER_LOW: Final[float] = 1.2
COMBO_GOLD_MULTIPLIER_MID: Final[float] = 1.5
COMBO_GOLD_MULTIPLIER_HIGH: Final[float] = 2.0

COMBO_HEAL_AT_MID: Final[int] = 5       # 10 combo: kucuk can yenilenmesi
# 20 combo: Yanki bir kademe iyilesir - bkz. systems/echo.py

# Vurus sesinin perdesi her 5 combo'da %3 yukselir (docs 5).
COMBO_PITCH_STEP: Final[float] = 0.03
COMBO_PITCH_PER: Final[int] = 5


# =============================================================================
# GAME FEEL - HITSTOP   (docs/dovus-sistemi.md 5 - BAGLAYICI)
# =============================================================================
HITSTOP_NORMAL: Final[int] = 3
HITSTOP_FINISHER: Final[int] = 7
HITSTOP_BOSS: Final[int] = 9
HITSTOP_KILL: Final[int] = 12


# =============================================================================
# GAME FEEL - EKRAN SARSINTISI   (docs/derinlestirme.md 1.1, 1.2)
# =============================================================================
# Sarsinti rastgele degil YONLU - darbe vektoru boyunca.
# Uc buyukluk kurali: rutin aksiyon kucuk, gercek olay buyuk.
SHAKE_DECAY: Final[float] = 0.85        # Her kare genlik bu oranla azalir (ustel)

SHAKE_NORMAL_PIXELS: Final[float] = 2.0
SHAKE_NORMAL_FRAMES: Final[int] = 4
SHAKE_NORMAL_ROTATION: Final[float] = 0.0    # Kucuk sarsintida rotasyon YOK

SHAKE_FINISHER_PIXELS: Final[float] = 5.0
SHAKE_FINISHER_FRAMES: Final[int] = 8
SHAKE_FINISHER_ROTATION: Final[float] = 0.4  # derece

SHAKE_BOSS_PIXELS: Final[float] = 9.0
SHAKE_BOSS_FRAMES: Final[int] = 12
SHAKE_BOSS_ROTATION: Final[float] = 0.8      # derece


# =============================================================================
# GAME FEEL - FLAS, SQUASH & STRETCH   (docs/derinlestirme.md 1.5)
# =============================================================================
HIT_FLASH_FRAMES: Final[int] = 2        # Hedef tamamen beyaz

SQUASH_JUMP: Final[tuple[float, float]] = (0.85, 1.15)      # (yatay, dikey)
SQUASH_JUMP_FRAMES: Final[int] = 3
SQUASH_LAND: Final[tuple[float, float]] = (1.20, 0.80)
SQUASH_LAND_FRAMES: Final[int] = 4
SQUASH_HIT: Final[tuple[float, float]] = (1.30, 0.70)
SQUASH_HIT_FRAMES: Final[int] = 2

SOUND_PITCH_VARIANCE: Final[float] = 0.08   # Her tekrarli efekt +-%8


# =============================================================================
# KAMERA   (docs/dovus-sistemi.md 5)
# =============================================================================
CAMERA_SMOOTHING: Final[float] = 0.12    # Hedefe yaklasma orani / kare
CAMERA_LOOKAHEAD_PIXELS: Final[float] = 12.0
CAMERA_DEADZONE_WIDTH: Final[float] = 36.0   # ayarlanabilir
CAMERA_DEADZONE_HEIGHT: Final[float] = 28.0  # ayarlanabilir


# =============================================================================
# DUSMAN   (docs/dovus-sistemi.md 6 - BAGLAYICI)
# =============================================================================
ENEMY_MIN_TELL_FRAMES: Final[int] = 14   # Her saldiri en az bu kadar once okunur
MAX_SIMULTANEOUS_ATTACKERS: Final[int] = 2   # Saldiri hakki sistemi

# Ritim imzalari - her tipin sabit, ogrenilebilir saldiri ritmi
# (docs/derinlestirme.md 4.2). Rastgele saldiran dusman ogrenilemez.
TELL_FRAMES_SHAMBLER: Final[int] = 18    # Suruklenen
TELL_FRAMES_CLIMBER: Final[int] = 16     # Tirmanan
TELL_FRAMES_BLOATED: Final[int] = 30     # Sismek uzun surer, patlama okunur

ENEMY_STAGGER_FRAMES: Final[int] = 14    # Poise kirilinca sendeleme suresi

# --- Saldiri hakki (token) ---------------------------------------------------
# Hakki olmayan dusman **kusatma yorungesinde** bekler. Kalabalik dovusun
# okunabilirligi buna dayaniyor: iki saldirgan izlenebilir, alti izlenemez.
TOKEN_HOLD_MIN_FRAMES: Final[int] = 24   # Hak alan en az bu kadar tutar
TOKEN_HOLD_MAX_FRAMES: Final[int] = 150  # Sonra birakir - sira kimsede kilitlenmesin
TOKEN_COOLDOWN_FRAMES: Final[int] = 30   # Birakan bu kadar tekrar isteyemez

# --- Kusatma yorungesi -------------------------------------------------------
ORBIT_RADIUS_MIN: Final[float] = 34.0    # Bu mesafeden yakina sokulmaz
ORBIT_RADIUS_MAX: Final[float] = 62.0
ORBIT_SLOT_WIDTH: Final[float] = 18.0    # Bekleyenler ust uste binmesin
ENEMY_APPROACH_SPEED: Final[float] = 0.55
ENEMY_ORBIT_SPEED: Final[float] = 0.30

# --- Algi --------------------------------------------------------------------
ENEMY_SIGHT_RANGE: Final[float] = 170.0
ENEMY_LOSE_RANGE: Final[float] = 240.0   # Histerezis: goz acip kapama olmasin

# --- Tip degerleri -----------------------------------------------------------
# Suruklenen - combo hedef tahtasi. Yavas 3'luk ritim: bekle-bekle-vur.
SHAMBLER_HEALTH: Final[int] = 40
SHAMBLER_POISE: Final[int] = 2
SHAMBLER_SPEED: Final[float] = 0.45
SHAMBLER_DAMAGE: Final[int] = 8
SHAMBLER_REACH: Final[int] = 14
SHAMBLER_ACTIVE_FRAMES: Final[int] = 4
SHAMBLER_RECOVER_FRAMES: Final[int] = 22
SHAMBLER_BEAT_FRAMES: Final[int] = 34    # Ritmin bir vurusu

# Tirmanan - dikey farkindalik. Ani tek vurus, uzun bekleme.
CLIMBER_HEALTH: Final[int] = 28
CLIMBER_POISE: Final[int] = 1            # Kirilgan - tek vurusta sendeler
CLIMBER_SPEED: Final[float] = 0.85
CLIMBER_DAMAGE: Final[int] = 10
CLIMBER_REACH: Final[int] = 12
CLIMBER_ACTIVE_FRAMES: Final[int] = 5
CLIMBER_RECOVER_FRAMES: Final[int] = 30  # Uzun bekleme - ritmin yarisi bu
CLIMBER_DROP_SPEED: Final[float] = 2.6
CLIMBER_TRIGGER_X: Final[float] = 20.0   # Oyuncu bu kadar altina girince birakir
# Isiktan kacma (docs/bolum-03.md Oda 3) - tavanda kayarak uzaklasir.
CLIMBER_FLEE_SPEED: Final[float] = 0.5

# Sismek - konumlandirma. Yaklas-sis-patla, sabit sure.
BLOATED_HEALTH: Final[int] = 34
BLOATED_POISE: Final[int] = 3
BLOATED_SPEED: Final[float] = 0.38
BLOATED_FUSE_FRAMES: Final[int] = 30     # TELL_FRAMES_BLOATED ile ayni ritim
BLOATED_TRIGGER_RANGE: Final[float] = 26.0
BLOATED_BLAST_RADIUS: Final[float] = 40.0
BLOATED_BLAST_DAMAGE: Final[int] = 18
BLOATED_SELF_DESTRUCT: Final[bool] = True

# --- Kalicilik ---------------------------------------------------------------
# Kan lekesi ve moloz bolum boyunca zeminde kalir (CLAUDE.md 7).
# Ust sinir var: 400 leke birikirse cizim bedeli hissedilir.
MAX_GROUND_DECALS: Final[int] = 220


# =============================================================================
# KARAKTER FARKLARI   (docs/dovus-sistemi.md 8 - BAGLAYICI)
# =============================================================================
REY_MOVE_MULTIPLIER: Final[float] = 1.15
REY_MAX_HEALTH: Final[int] = 80
REY_CHAIN_WINDOW: Final[int] = 14        # Comert
REY_DODGE_CHARGES: Final[int] = 2

ARDO_MOVE_MULTIPLIER: Final[float] = 0.90
ARDO_MAX_HEALTH: Final[int] = 120
ARDO_CHAIN_WINDOW: Final[int] = 10       # Siki
ARDO_DODGE_CHARGES: Final[int] = 1


# =============================================================================
# YANKI   (docs/gdd.md 4)
# =============================================================================
ECHO_TIER_CLEAR: Final[int] = 2          # Berrak
ECHO_TIER_MURKY: Final[int] = 1          # Bulanik
ECHO_TIER_SILENT: Final[int] = 0         # Sessiz - dip, daha asagi inmez

ECHO_VIGNETTE_STRENGTH: Final[float] = 0.55   # Aktifken ekran kenari kararmasi
ECHO_DAMAGE_TAKEN_MULTIPLIER: Final[float] = 1.25   # Aktifken savunma duser
ECHO_MUFFLE_VOLUME: Final[float] = 0.55       # Sesler boguklasir


# =============================================================================
# EKONOMI   (docs/ekonomi-uretim.md 1)
# =============================================================================
GOLD_ENEMY_MIN: Final[int] = 3
GOLD_ENEMY_MAX: Final[int] = 8
GOLD_MINIBOSS_MIN: Final[int] = 40
GOLD_MINIBOSS_MAX: Final[int] = 60
GOLD_BOSS_MIN: Final[int] = 150
GOLD_BOSS_MAX: Final[int] = 250
GOLD_CHEST_MAIN_MIN: Final[int] = 25
GOLD_CHEST_MAIN_MAX: Final[int] = 40
GOLD_CHEST_SECRET_MIN: Final[int] = 60
GOLD_CHEST_SECRET_MAX: Final[int] = 100

DEATH_GOLD_LOSS_RATIO: Final[float] = 0.30   # Olunce dusen, yerde kalir


# =============================================================================
# UI   (CLAUDE.md 9)
# =============================================================================
MENU_TRANSITION_MAX_FRAMES: Final[int] = 12   # Hicbir menu gecisi bunu asmaz
HUD_HEALTH_VISIBLE_FRAMES: Final[int] = 180   # Hasardan sonra 3 saniye
FAST_FORWARD_MULTIPLIER: Final[float] = 3.0   # Basili tutunca gecis hizlanir


# =============================================================================
# ISIK   (docs/bolum-03.md - "Meşale Mahzeni")
# =============================================================================
# Karanlik ≠ siyah: en koyu palet rengi + hafif mavi ton kullanilir, ve
# karanlikta bile siluetler bu kadar alfa ile hafifce secilir (docs 03,
# "Uygulama Notlari").
DARKNESS_SILHOUETTE_ALPHA: Final[float] = 0.08

TORCH_LIGHT_RADIUS: Final[float] = TILE_SIZE * 3.0     # "3 tile'lik bir daire"
PURPLE_FLAME_LIGHT_RADIUS: Final[float] = TORCH_LIGHT_RADIUS * 2.0

TORCH_THROW_SPEED: Final[float] = 3.2        # piksel / kare, yatay
TORCH_THROW_LIFT: Final[float] = -3.6        # piksel / kare, yukari - yay cizer

# Ses haritasi (sonar). `ask()` ile ayni desen: cooldown + gosterim suresi,
# ama tek seferlik genisleyen bir halka - surekli acilma/kapanma egrisi
# degil (docs/bolum-03.md Oda 2).
SONAR_COOLDOWN_FRAMES: Final[int] = 90
SONAR_PULSE_FRAMES: Final[int] = 60          # 1 saniye - genisleyip soner
SONAR_MAX_RADIUS: Final[float] = 140.0

# Mum Bekcisi ticareti - sabit uc teklif (docs/bolum-03.md Oda 3-A).
CANDLE_KEEPER_PRICE_TORCH: Final[int] = 40
CANDLE_KEEPER_PRICE_ETERNAL_WICK: Final[int] = 120     # "Sonmez Fitil"
CANDLE_KEEPER_PRICE_DEATH_CANDLE: Final[int] = 200     # Olum korumasi

# Sonmus Olan - Bolum 3 mini-boss. Uc hamle: Karanlik Dalgasi/Surukleme/
# Mum Cagrisi. Mangal yanarken sersemler - combo penceresi.
EXTINGUISHED_ONE_HEALTH: Final[int] = 200
EXTINGUISHED_ONE_POISE: Final[int] = 5
DARK_WAVE_TELL_FRAMES: Final[int] = 20       # "kollarini acar" - 20 kare tell
DARK_WAVE_BLACKOUT_FRAMES: Final[int] = 120  # 2 saniye tam karanlik
DRAG_TELL_FRAMES: Final[int] = 16
CANDLE_CALL_TELL_FRAMES: Final[int] = 26
BRAZIER_STAGGER_FRAMES: Final[int] = 90      # Yanma anindaki sersemleme suresi
BRAZIER_BURN_FRAMES: Final[int] = 300        # Kendiliginden sonene kadar (5 sn)
BRAZIER_LIGHT_RADIUS: Final[float] = TILE_SIZE * 2.5
DRAG_SNUFF_RANGE: Final[float] = TILE_SIZE * 1.5   # Surukleme mangala buraya kadar yakinsa sonduruyor

CHAPTER3_CHEST_GOLD_ROOM2: Final[int] = 35
CHAPTER3_CHEST_GOLD_SECRET: Final[int] = 70
CHAPTER3_BOSS_GOLD: Final[int] = 70

# Fener tilsimi - mini-boss odulu.
FENER_LIGHT_RADIUS_BONUS: Final[float] = 0.40
FENER_DARK_DAMAGE_BONUS: Final[float] = 0.10
