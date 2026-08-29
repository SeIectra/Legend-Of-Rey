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
# SILAHLAR - yumruktan kilica  (Arda karari, 22.08.2026)
# =============================================================================
# Rey artik tamamen silahsiz baslamiyor: **yumrukla** basliyor, kilici
# Bolum 1'de buluyor. Bolum 2 mini-boss sonrasi Hancer/Balta secimi
# (DEVIR.md acik madde 9) ayni altyapiyi (`src/combat/weapons.py`)
# kullanacak; ileride yay/arbalet de eklenebilir (mimari bunu engellemiyor,
# icerik olarak henuz yazilmadi - sirasi gelmedi).
#
# Kilicin tablosu (`CHAIN`, yukarida) BAGLAYICI (docs/dovus-sistemi.md).
# Asagidakiler **yer tutucu** - Arda ile birlikte gercek degerlere
# oturtulacak; CLAUDE.md'nin "sessizce degistirme" yasagi zaten
# belirlenmis sayilar icin - bunlar henuz hic belirlenmedi.
FIST_CHAIN: Final[tuple[ChainHit, ...]] = (
    ChainHit(windup=5, active=3, recovery=12, damage=4, knockback=1.0,
             cancelable=True, hitstop=2),
)
DAGGER_CHAIN: Final[tuple[ChainHit, ...]] = (
    ChainHit(windup=3, active=2, recovery=6, damage=7, knockback=1.1,
             cancelable=True, hitstop=2),
    ChainHit(windup=3, active=2, recovery=7, damage=8, knockback=1.2,
             cancelable=True, hitstop=3),
    ChainHit(windup=4, active=3, recovery=10, damage=13, knockback=2.2,
             cancelable=False, hitstop=5),
)
AXE_CHAIN: Final[tuple[ChainHit, ...]] = (
    ChainHit(windup=7, active=4, recovery=15, damage=17, knockback=2.8,
             cancelable=True, hitstop=4),
    ChainHit(windup=9, active=5, recovery=20, damage=32, knockback=5.5,
             cancelable=False, hitstop=9),
)


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
# Bu kadar havada kalinca inis "land_hard" calar, azi "land_soft"
# (assets/audio/SES-LISTESI.md 2). `Player._update_ground_state()` zaten
# `air_frames > 10` olmadan hic cagirmiyor - bu esik onun USTUNDE.
HARD_LAND_AIR_FRAMES: Final[int] = 30
# Gecis kareleri (src/art/animation.py::_land/_turn). Ikisi de KISA:
# oynanisi kilitlemiyorlar, yalnizca o kadar kare boyunca gecis pozu
# cizilyor. Uzun tutulsalardi hareket agir cekim gorunurdu.
LAND_FRAMES_SOFT: Final[int] = 7      # Normal inis
LAND_FRAMES_HARD: Final[int] = 12     # Yuksekten inis - daha uzun toparlanir
TURN_FRAMES: Final[int] = 8           # Kosarken yon degistirme pivotu
TURN_PIVOT_MIN_SPEED: Final[float] = 0.9   # Bu hizin altinda pivot yok
# Kac piksel yol alinca bir adim sesi caliyor (Player._update_footsteps).
# Yuruyus hizinin dogal bir sonucu olsun diye kare sayisi degil mesafe.
# Ilk deger (11px) kosarken saniyede ~11 adim sesi veriyordu - rahatsiz
# edici derecede sik (Arda'nin canli oynanis geri bildirimi, 22.08.2026).
# 42px ~2.5 adim/sn - gercekci bir kosu ritmine yakin.
STEP_DISTANCE_PX: Final[float] = 42.0
# Kolye pusulasi hedefe kilitliyken bu isinma esiginin ustunde kalp atisi
# duyulur (assets/audio/SES-LISTESI.md 4). Sifir = her zaman duyulur;
# cok dusuk tutuluyor ki uzaktaki hafif bir titresim de fark edilsin.
NECKLACE_BEAT_MIN_WARMTH: Final[float] = 0.02


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

# Dikey erisim payi.  # ayarlanabilir - belgede yok, hata raporundan geldi
# `distance_to()` yalnizca yatay olcuyor (docs/dovus-sistemi.md 6'nin
# tasarladigi gibi - dusman gorusu ekran genisligine gore dusunulmus).
# Ama bu yuzden bir dusman havadaki kopuk bir platforma (ornegin guclu bir
# knockback_up ile) inince, oyuncu tam altindaysa yatay mesafe hep kucuk
# kaliyor ve dusman ulasamayacagi bir hedefe sonsuza dek saldiri denemesi
# yapiyordu - "ust platformlara sikisma" raporunun kaynagi buydu. Saldiri
# **baslatma** karari bu payla dikeyde de sinirlaniyor; gorus/kusatma
# davranisi (ekran capinda "farkinda olma" hissi) bilerek degismiyor.
ENEMY_VERTICAL_ENGAGE_RANGE: Final[float] = 28.0

# O onceki fix'in **acikca birakilan** yarim tarafi: dusman artik bosuna
# saldirmiyor ama erisilemez bir platformda sonsuza kadar bekleyebiliyordu -
# "yapisik dusman" olarak geri bildirildi (Arda, 22.08.2026). Bu kadar kare
# erisilemez kaldiktan sonra dusman en yakin kenari arayip oradan duser.
ENEMY_UNREACHABLE_PATIENCE_FRAMES: Final[int] = 90
# Kenar arama menzili (tile) - bu kadar ileride zemin kesiliyorsa "kenar"
# sayilir. Cok kucuk olursa dusman kenari gecmeden fark edemez (duz zeminde
# sonsuza dek arar), cok buyuk olursa uzak bir bosluga yanlislikla yonelir.
ENEMY_LEDGE_PROBE_TILES: Final[int] = 2

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
# Oyuncu tam altina hic girmezse (oda gecisi bunu garanti etmiyor) Tirmanan
# sonsuza kadar tavanda asili kalirdi - "yapisik dusman" gibi okunuyordu
# (Arda'nin canli oynanis geri bildirimi, 22.08.2026). Bu kadar kare
# boyunca farkinda ama tetiklenmediyse yine de birakir.
CLIMBER_PATIENCE_FRAMES: Final[int] = 150
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


# =============================================================================
# BOLUM 4 - KAYIT ODASI   (docs/yapi.md B4 - "★nefes")
# =============================================================================
# Dovus yok. Butun sayilar **zamanlama** sayisi: bir seyin ne kadar surdugu,
# ne kadar yakindan fark edildigi. Hicbiri denge degeri degil.

# Kelimesiz gunluk: bir sayfa bu kadar kare ekranda kalir, sonra kendi
# kendine cevrilir. 150 kare = 2.5 saniye - bir resmi okumaya yetiyor,
# oyuncuyu tutmaya yetmiyor. Tusa basmak gerekmiyor: gunlukte tek kelime
# yok, o yuzden "cevir" diyen bir yazi da olamaz (docs/yapi.md: jestle
# anlatim). Yaklasinca acilir, uzaklasinca kapanir.
JOURNAL_PAGE_FRAMES: Final[int] = 150
JOURNAL_FADE_FRAMES: Final[int] = 12          # Acilma/kapanma - menu kurali
JOURNAL_NEAR_RANGE: Final[float] = TILE_SIZE * 2.0

# Kamp: sonmus atesin basinda dinlenme. Iyilesme + yetenek agaci kancasi.
CAMP_NEAR_RANGE: Final[float] = TILE_SIZE * 1.5

# Yarim harita bu kadar yakindan alinir - dokununca, tusa basmadan
# (src/world/pickups.py'nin sandik gerekcesiyle ayni: odulle oyuncu
# arasina tus koymak yalnizca kaciran oyuncu uretir).
HALF_MAP_PICKUP_RANGE: Final[float] = TILE_SIZE * 1.2

# Kolye ani - "sessiz karakter ani" (docs/yapi.md B4). Kelimesiz.
# 180 kare = 3 saniye: bir jestin okunmasi icin yeterli, oyuncunun
# kontrolu kaybettigini hissetmesi icin kisa. Oynanis durmuyor - oyuncu
# yurumeye devam edebilir, an onun etrafinda olup bitiyor.
NECKLACE_MOMENT_RANGE: Final[float] = TILE_SIZE * 1.5
NECKLACE_MOMENT_FRAMES: Final[int] = 180
# Yanki kademesi anin **sonunda** geri geliyor (docs/gdd.md 4: "Kademe
# kazanimi: kontrol noktalari ve nefes bolumleri"). Basinda verilseydi
# toast jestin uzerine binerdi.
NECKLACE_RESTORE_AT: Final[int] = 150


# =============================================================================
# YETENEK AGACI   (docs/gdd.md 6 - "3 dal x 4 seviye", docs/yapi.md B4)
# =============================================================================
# **Hicbir deger asagidaki baglayici tabanlari degistirmiyor.** Yetenekler
# CHAIN, DODGE_*, CHAIN_WINDOW_FRAMES gibi belgelenmis kare degerlerinin
# USTUNE biner (carpan ya da bonus); taban sayilar oldugu gibi kalir.
SKILL_BRANCH_LEVELS: Final[int] = 4     # docs/gdd.md 6: dal basina dort seviye

# Seviye basina bedel (yetenek puani). Bir dalin tamami 1+1+2+2 = 6 puan.
# `docs/ekonomi-uretim.md` 1 oyun boyunca kabaca **6 yetenek puani**
# ongoruyor: yani butun butce ya tek bir dali dibine kadar acar, ya da uc
# dalin ilk iki seviyesini. Secim gercek bir secim - agacin tamami 18 puan
# eder ve asla toplanamaz.
SKILL_COST_BY_LEVEL: Final[tuple[int, ...]] = (1, 1, 2, 2)

# --- Dal 1: KESKIN (dovus) ---------------------------------------------------
SKILL_EDGE_DAMAGE_BONUS: Final[float] = 0.06     # Kosulsuz hasar
SKILL_FLOW_CHAIN_FRAMES: Final[int] = 2          # Zincir penceresine EK kare
SKILL_MOMENTUM_DAMAGE_BONUS: Final[float] = 0.15  # COMBO_THRESHOLD_MID ustunde
SKILL_FINISHER_DAMAGE_BONUS: Final[float] = 0.25  # Yalniz bitirici vurusta

# --- Dal 2: YANKI (Rey'in laneti) --------------------------------------------
# Ardo bu dali oynamaz - Yanki'yi duymuyor (DEVIR.md 3.7). Etkiler onda
# sessizce 1.0 doner; `branch_usable()` ekranin bunu gostermesini sagliyor.
SKILL_REACH_SIGHT_BONUS: Final[float] = 0.25     # Gorus menzili
SKILL_WARD_DEFENCE_RELIEF: Final[float] = 0.12   # Yanki ACIKKEN alinan hasar
SKILL_GRIP_SIGHT_BONUS: Final[float] = 0.30      # Gorus menzili (ikinci kat)
SKILL_MEND_COMBO_RELIEF: Final[int] = 6          # COMBO_TO_RESTORE'dan dusulur

# --- Dal 3: TAS (dayaniklilik) -----------------------------------------------
SKILL_HIDE_HEALTH_BONUS: Final[int] = 5          # docs/gdd.md 6: "+5 can"
SKILL_GUARD_DEFENCE_RELIEF: Final[float] = 0.06  # Kosulsuz alinan hasar
SKILL_ROLL_DODGE_CHARGES: Final[int] = 1         # Kacinma sarji
SKILL_WILL_HEALTH_BONUS: Final[int] = 10
SKILL_WILL_DEFENCE_RELIEF: Final[float] = 0.08

# Bolum 4'te kampta dinlenince verilen yetenek puani. Bir tane: oyuncu
# agaci ilk kez gorurken harcayacak bir seyi olsun ama secim ANLAMLI
# kalsin - uc dalin ilk dugumu de 1 puan, yani ilk karar "hangi dal"
# sorusunun kendisi.
REST_SKILL_POINTS: Final[int] = 1


# --- SU SEVIYESI (Bolum 5, src/world/water.py) ------------------------------
# Vana cevrilince su hedefe bu hizla yaklasir (piksel/kare). 0.35 =
# saniyede ~21 piksel, yani bir tile ~0.75 saniyede. Ani sicrama okunmaz
# ve tehlikeli olurdu; cok yavasi da bulmacayi bekleme oyununa cevirir.
WATER_LEVEL_SPEED: Final[float] = 0.35
# Kaldirma kuvveti: tam batmis govdenin yercekimi bu oranda azalir.
# 0.86 = %14'u kaliyor - hafif batma "yuzmek icin tusa bas" diyor.
# 1.0 olsaydi oyuncu suda asili kalirdi ve yuzme bir SECIM olmazdi.
WATER_BUOYANCY: Final[float] = 0.86
# Suda dusus hizi tavani (piksel/kare). Yoksa derin suya giren oyuncu
# dibe cakiliyor ve su "hava" gibi hissettiriyordu.
WATER_MAX_SINK_SPEED: Final[float] = 0.9
# Yatay surtunme orani - suda hareket agir.
WATER_DRAG_X: Final[float] = 0.12
# Yuzerken yukari hiz. Ziplama hizindan (PLAYER_JUMP_SPEED) belirgin
# dusuk: su yukselmeyi YAVASLATIYOR, engellemiyor.
WATER_SWIM_SPEED: Final[float] = 1.05
# Yuzey dalgasinin genligi (piksel). Duz bir cizgi "su" degil "zemin"
# gibi okunuyordu.
WATER_SURFACE_WAVE: Final[float] = 1.4


# --- KALKANLI (Katman 2'nin ilk uyesi, src/entities/enemies/shieldbearer.py) -
# `docs/gdd.md` 7: *"Kalkanli - onden vurulmaz, arkaya gec."* Katman 2'nin
# sorusu **combo'yu KIRMAYI ogren**; Kalkanli o dersi onden veriyor.
SHIELDBEARER_HEALTH: Final[int] = 52     # Katman 1'in hepsinden dayanikli
SHIELDBEARER_POISE: Final[int] = 4       # Kalkani dusunce bile kolay sendelemez
SHIELDBEARER_SPEED: Final[float] = 0.38  # Yavas - tehdit hizdan degil kalkandan
SHIELDBEARER_DAMAGE: Final[int] = 11
SHIELDBEARER_REACH: Final[int] = 15
SHIELDBEARER_ACTIVE_FRAMES: Final[int] = 5
# Uzun toparlanma **bilincli**: kalkan indiginde acilan pencere bu.
# Oyuncunun ikinci gecerli cevabi ("saldiriyi yemle, toparlanirken vur")
# tam olarak bu sayidan doguyor. Kisaltmak dersi tek cevaba indirger.
SHIELDBEARER_RECOVER_FRAMES: Final[int] = 38
TELL_FRAMES_SHIELDBEARER: Final[int] = 24  # Agir ve okunur (alt sinir 14)
# Oyuncu arkasina gectikten sonra donmesi bu kadar surer. **Bulmacanin
# tek ayar dugmesi bu.** Aninda donseydi arkaya gecmek imkansiz olurdu;
# cok uzun olsaydi Kalkanli bir dusman degil bir tahta kukla olurdu.
# 34 kare ~0.57 saniye: iki vurusluk pencere, ucuncuye yetmez.
SHIELDBEARER_TURN_FRAMES: Final[int] = 34
# Donusun kendisi de okunur olmali - donmeden once bu kadar kare parlar.
SHIELDBEARER_TURN_TELL_FRAMES: Final[int] = 10
# Kalkana carpan oyuncu bu kadar geri itilir (piksel/kare). Zarar YOK -
# ceza hasar degil, ritmini kaybetmek.
SHIELDBEARER_BLOCK_PUSHBACK: Final[float] = 1.9


# --- IZ SURME (Ardo'nun karsi mekanigi, src/systems/tracking.py) -------------
# `docs/derinlestirme.md` 2.4: *"Rey gelecegi/gizliyi duyar, Ardo gecmisi
# gorur."* Ayni tus, zit bilgi.
#
# Egri **bilerek Yanki ile ayni** (`echo.py` RISE_FRAMES=14/FALL=20):
# acilirken hizli, kapanirken yavas. Iki karakterin girdisi ayni
# hissetmeli - ayrilan sey duyu, tempo degil.
TRACKING_RISE_FRAMES: Final[int] = 14
TRACKING_FALL_FRAMES: Final[int] = 20
# Okuma menzili (piksel). Yanki kademeye gore 260 / 96 / 0 (`echo.py`
# SIGHT_RANGE); Iz Surme **sabit 190** - ikisinin arasinda.
#
# Asimetri bilincli: Yanki bir LANET, olumle zayifliyor ve dibi sessizlik.
# Ardo'nun laneti yok, o yuzden Iz Surme hic zayiflamiyor - ama hicbir
# zaman berrak bir Yanki kadar da gormuyor. "Guvenilir ama sinirli"ya
# karsi "cok guclu ama kirilgan": ayni zindani iki farkli risk profiliyle
# okuyorlar.
TRACKING_RANGE: Final[float] = 190.0
# **Bedel**: Iz Surme acikken yasayan dusmanlar bu oranda soluyor. Ardo
# gecmise bakarken simdiyi net goremiyor. Savunmaya DOKUNMUYOR - iki
# karakterin bedeli ayni kanaldan gelseydi mekanikler ayni sey olurdu.
TRACKING_ENEMY_FADE: Final[float] = 0.62
# Bir aktor kac karede bir ayak izi birakir. Her karede biraksaydi hem
# liste dolardi hem "iz" degil "cizgi" cizerdi.
TRACKING_STEP_FRAMES: Final[int] = 16
# Ayni anda tutulan azami iz. Asilinca en eskisi dusuyor.
TRACE_MAX: Final[int] = 400
# Iz bu kadar karede tamamen solar (gorsel - iz SILINMIYOR, sadece
# soluyor). 3600 = bir dakika: taze bir iz "az once buradaydi", soluk bir
# iz "cok once" diyor. Yasin okunabilmesi bilginin yarisi.
TRACE_FADE_FRAMES: Final[int] = 3600
