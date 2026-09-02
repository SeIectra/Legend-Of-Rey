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

# --- Mizrakli (Katman 2, Bolum 10) -------------------------------------------
# Kalkanli **yonle** soruyordu (arkaya gec); Mizrakli **mesafeyle**:
# senin menzilinin disindan vuruyor. Ayni ders, baska bir fizik sorusu.
SPEARMAN_HEALTH: Final[int] = 42         # Kalkanli'dan az - zirhi yok
SPEARMAN_POISE: Final[int] = 2           # Kolay sendeliyor: iceri giren kazaniyor
SPEARMAN_SPEED: Final[float] = 0.44
SPEARMAN_DAMAGE: Final[int] = 9
# **Uzun** menzil - oyuncunun kilic menzili ~16. Fark mekanigin kendisi.
SPEARMAN_REACH: Final[int] = 34
# Bundan yakinsa geri adim atiyor. Menzilin yarisindan biraz fazla:
# oyuncu "girdim" hissini yasayacak kadar yaklasabilmeli.
SPEARMAN_MIN_RANGE: Final[int] = 22
SPEARMAN_BACKSTEP_SPEED: Final[float] = 0.62
# Tell uzun: uzun menzilli bir saldiri **okunabilir** olmali, yoksa
# oyuncu neden vuruldugunu anlamiyor (CLAUDE.md 7: en az 14 kare).
SPEARMAN_TELL_FRAMES: Final[int] = 22
SPEARMAN_ACTIVE_FRAMES: Final[int] = 6
# Toparlanma penceresi: iceri giren oyuncunun iki vurus yapacagi sure.
SPEARMAN_RECOVER_FRAMES: Final[int] = 34
# Ceza can degil **mesafe**: kapatmak icin harcadigin yolu geri veriyorsun.
SPEARMAN_PUSHBACK: Final[float] = 3.4


# --- Okcu (Katman 2, "uzaktan bozar, once susturulmali") ---------------------
# Tehdit oldugu YER degil oldugu AN: yakin dovusun ortasinda gelen bir
# ok zinciri kiriyor. Kendisi zayif; cozum ona oncelik vermek.
ARCHER_HEALTH: Final[int] = 30           # Katman 2'nin en kirilgani
ARCHER_POISE: Final[int] = 1
ARCHER_SPEED: Final[float] = 0.5
ARCHER_DAMAGE: Final[int] = 6            # yakin dovuste - zayif
ARCHER_REACH: Final[int] = 14
# Atis menzili: neredeyse bir ekran. Uzaklik onun tek silahi.
ARCHER_SHOT_RANGE: Final[int] = 150
# Oyuncu bundan yakinsa **kaciyor** - "ona kos" cozumu calissin diye.
ARCHER_FLEE_RANGE: Final[int] = 52
ARCHER_FLEE_SPEED: Final[float] = 0.72
ARCHER_TELL_FRAMES: Final[int] = 26      # yay geriliyor - uzun ve okunur
ARCHER_ACTIVE_FRAMES: Final[int] = 4
ARCHER_RECOVER_FRAMES: Final[int] = 30
ARCHER_ARROW_SPEED: Final[float] = 3.6
ARCHER_ARROW_DAMAGE: Final[int] = 8
ARCHER_ARROW_LIFE: Final[int] = 90       # ~1.5 sn sonra dusuyor

# --- Komutan (Katman 2, "takviye cagirir") -----------------------------------
# Kendisi zayif, cagirdiklari degil. Ust sinir sart: sinirsiz olsaydi
# zorluk beceriyle TERS orantili olurdu.
COMMANDER_HEALTH: Final[int] = 46
COMMANDER_POISE: Final[int] = 2          # kesilebilir olmali
COMMANDER_SPEED: Final[float] = 0.34
COMMANDER_DAMAGE: Final[int] = 8
COMMANDER_REACH: Final[int] = 15
# Cagirma menzili genis: oyuncuyla temas etmeden cagiriyor.
COMMANDER_SUMMON_RANGE: Final[int] = 120
COMMANDER_TELL_FRAMES: Final[int] = 34   # en uzun tell - kesilebilsin
COMMANDER_ACTIVE_FRAMES: Final[int] = 6
COMMANDER_RECOVER_FRAMES: Final[int] = 46
COMMANDER_SUMMON_LIMIT: Final[int] = 3

# --- Sessiz (Katman 3, "Yanki onu gostermez") --------------------------------
# Yeni hamlesi yok; tek ozelligi Yanki'nin siluetinde bulunmamasi.
SILENT_HEALTH: Final[int] = 34
SILENT_POISE: Final[int] = 2
SILENT_SPEED: Final[float] = 0.4
SILENT_DAMAGE: Final[int] = 12           # pusu - vurusu agir
SILENT_REACH: Final[int] = 14
# Pusudan bu mesafede kalkiyor. Kisa: "pusu" olmasi icin oyuncunun
# ona gercekten yaklasmis olmasi gerek.
SILENT_AMBUSH_RANGE: Final[int] = 46
SILENT_TELL_FRAMES: Final[int] = 16
SILENT_ACTIVE_FRAMES: Final[int] = 5
SILENT_RECOVER_FRAMES: Final[int] = 26

# --- Yankilayan (Katman 3, "sahte ipucu verir") ------------------------------
ECHOING_HEALTH: Final[int] = 38
ECHOING_POISE: Final[int] = 2
ECHOING_SPEED: Final[float] = 0.42
ECHOING_DAMAGE: Final[int] = 9
ECHOING_REACH: Final[int] = 15
ECHOING_TELL_FRAMES: Final[int] = 18
ECHOING_ACTIVE_FRAMES: Final[int] = 5
ECHOING_RECOVER_FRAMES: Final[int] = 28
# Sahte isaret kendisinin ARKASINA konuyor - oyuncu ona giderken
# yanindan gecmek zorunda.
ECHOING_HINT_RANGE: Final[int] = 70
ECHOING_HINT_LIFE: Final[int] = 150      # ~2.5 sn

# --- Bolunen (Katman 3, "vurunca ikiye ayrilir") -----------------------------
# Ders "combo yapma" degil **"combo'yu bitir"**: bitirici vurus
# bolmuyor. Aksi halde oyuncu dovusmekten kacinirdi.
SPLITTER_HEALTH: Final[int] = 40
SPLITTER_POISE: Final[int] = 1
SPLITTER_SPEED: Final[float] = 0.46
SPLITTER_DAMAGE: Final[int] = 8
SPLITTER_REACH: Final[int] = 14
SPLITTER_TELL_FRAMES: Final[int] = 16
SPLITTER_ACTIVE_FRAMES: Final[int] = 5
SPLITTER_RECOVER_FRAMES: Final[int] = 24
# Kac kez bolunebilir. 2 = en fazla dort kucuk parca; ucuncu nesil tek
# vurusla oluyor, yani kisa bir final.
SPLITTER_GENERATIONS: Final[int] = 2
SPLITTER_SPLIT_PUSH: Final[float] = 1.5


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


# --- YOLDAS (Bolum 6, src/entities/companion.py) -----------------------------
# `docs/gdd.md` 8: B6 "Ardo'yla ilk beraber dovus". Yoldas oynamiyor,
# YARDIM EDIYOR - asagidaki uc sayi o farki tutuyor.
COMPANION_HEALTH: Final[int] = 90
# Vurus araligi seyrek: dusmani temizlemez, mesgul eder. Oyuncunun
# zincir penceresi 12 kare; yoldas onun bes katinda bir vuruyor.
COMPANION_ATTACK_COOLDOWN: Final[int] = 62
# Hasar oyuncunun ilk vurusunun (10) altinda. Oldurme oyuncunun isi.
COMPANION_DAMAGE: Final[int] = 7
COMPANION_ATTACK_RANGE: Final[float] = 20.0
# Savurmadan once okunur an. Dusmanin tell'i degil ama oyuncu yoldasin
# ne yaptigini gorebilmeli - yoksa hasar "havadan" geliyor gibi olur.
COMPANION_TELL_FRAMES: Final[int] = 12
COMPANION_SPEED: Final[float] = 1.05
# Oyuncudan bu kadar uzaktaki dusmani kovalamaz. Tasma olmasaydi yoldas
# odanin obur ucuna gider ve "nerede bu ya" hissi olusurdu.
COMPANION_LEASH: Final[float] = 120.0
# Cani bitince OLMEZ, diz coker ve bu kadar kare sonra kalkar. Olmesi
# dovusu bir koruma gorevine cevirirdi; ayrica agirlik plakasi bulmacasi
# cozulemez hale gelirdi.
COMPANION_DOWN_FRAMES: Final[int] = 210
# Emredilen noktaya bu kadar yaklasinca "durdu" sayiliyor.
COMPANION_HOLD_TOLERANCE: Final[float] = 10.0

# --- IKILI KONTROL (Bolum 17, src/systems/duo.py) ----------------------------
# `docs/yapi.md` mekanik 10: *"Karakterler arasi gecis, biri kolu tutar
# biri gecer."*
#
# Iki gecis arasi bekleme. Gerekli degil ama faydali: beklemesiz
# birakilinca tusa hizli basan oyuncu kamerayi iki nokta arasinda
# titretiyor. 18 kare (0,3 sn) kacinmanin toplam suresiyle ayni - oyunun
# zaten ogrettigi bir ritim.
#
# Uzun tutmak yanlis olurdu: bulmacayi cozerken gecis SIK yapiliyor ve
# her seferinde beklemek bulmacayi degil tusu zorlastirirdi.
SWITCH_COOLDOWN: Final[int] = 18

# --- ASIST KOMBO (Bolum 16) --------------------------------------------------
# `docs/yapi.md` B16: *"En uzun team-up. **Asist kombolar zirvede.**"*
#
# Oyuncu bitiriciyi vurdugunda yoldas beklemesini ATLAYIP ayni ana
# katiliyor. Tek vurus degil, tek **an**: `CLAUDE.md` 7'nin "uclu
# senkron" kurali (hitstop + sarsinti + parcacik tek yerden) burada
# dorde cikiyor.
#
# Tell kisa: yoldas bir dusman degil, oyuncunun okumasi gereken bir
# tehdit degil. Uzun tell asisti bitiriciden KOPARIR ve senkron hissi
# giderdi - anin butun degeri ayni karede olmasi.
COMPANION_ASSIST_TELL: Final[int] = 5
# Asist hasari normalin iki kati. Yoldas hala oldurmuyor (oyuncunun
# isi) ama bitiriciye katildiginda farki hissedilmeli - yoksa asist
# yalnizca bir animasyon olurdu.
COMPANION_ASSIST_DAMAGE: Final[int] = 14

# --- KALDIRMA (Bolum 16, src/systems/rescue.py) ------------------------------
# `docs/yapi.md` B16: *"Ama bu sefer **Rey de onu kurtarir.** Karsilikli."*
# `docs/gdd.md` 11 romantik yay: *"B16 | Esitlik | Sen onu
# kurtariyorsun."*
#
# B6'dan beri yoldas diz cokup KENDI KENDINE kalkiyordu ve oyuncu onun
# icin hicbir sey yapmiyordu. B16 bunu tersine ceviriyor: orada yoldas
# yalnizca sen kaldirirsan kalkiyor (`Companion.self_recovers = False`).
#
# Tutma suresi: bir dovusun ortasinda kipirdamadan durmak GERCEK bir
# risk olmali - anin butun anlami bu. 48 kare (0,8 sn) oyuncunun iki
# dusman arasinda bir bosluk aramasini gerektiriyor ama can sikici
# degil. Kacinma toplam 18 kare, dusman tell'i en az 14 - yani tutma
# suresi bir tell'den uzun: basladigin an guvendeysen bitirebiliyorsun.
RESCUE_HOLD_FRAMES: Final[int] = 48
# Bu mesafeden yakin olmali. Yoldas govdesi 12 piksel; 22 hem affedici
# hem "yaninda duruyorsun" hissini koruyor.
RESCUE_RANGE: Final[float] = 22.0
# Kaldirinca donen can. Kendi kalkmasindan (max/2 = 45) FAZLA: senin
# elinle kalkmak daha iyi olmali, yoksa kaldirmanin bir bedeli olur da
# karsiligi olmazdi.
RESCUE_HEALTH: Final[int] = 60

# --- AGIRLIK PLAKASI (Bolum 6, src/world/plate.py) ---------------------------
# `docs/gdd.md` 9 mekanik 4: *"Agirlik plakalari | B6 | Yaratik cesedini/
# sandigi plakaya surukle"*, `docs/yapi.md`: *"ikisi ayri plakada durmali -
# beraberlik mekaniğe giriyor"*.
PLATE_WIDTH: Final[int] = 20
PLATE_HEIGHT: Final[int] = 4
# Plaka basildiktan sonra bu kadar kare daha basili sayilir. Sifir
# olsaydi iki kisinin ayni KAREDE basmasi gerekirdi - imkansiza yakin
# ve adaletsiz. Yarim saniyelik tolerans bulmacayi "es zamanli" degil
# "birlikte" yapiyor.
PLATE_GRACE_FRAMES: Final[int] = 30


# --- BOSS 1: CURUMUS OLAN (Bolum 6, src/entities/bosses/rotted_one.py) -------
# Katman 1'in finali. Uc fazin her biri bir Katman 1 dusmanini geri
# getiriyor: Suruklenen (yer ritmi), Tirmanan (tavandan dusus), Sismek
# (yavru + patlama). Yeni bir sey OGRETMIYOR - tierin sinavini yapiyor.
ROTTED_HEALTH: Final[int] = 420
ROTTED_POISE: Final[int] = 8             # Combo'yu kolayca kirdirmiyor

ROTTED_SWEEP_DAMAGE: Final[int] = 16
ROTTED_SWEEP_REACH: Final[int] = 40      # Genis - kacinmayla gecilir
ROTTED_LUNGE_DAMAGE: Final[int] = 18
ROTTED_LUNGE_SPEED: Final[float] = 4.6   # Mesafe acarak gecilir
ROTTED_DROP_DAMAGE: Final[int] = 20
ROTTED_DROP_SPEED: Final[float] = 5.0
ROTTED_CLIMB_FRAMES: Final[int] = 46     # Tavanda asili kaldigi sure
ROTTED_SPAWN_COUNT: Final[int] = 2
# Patlama YONSUZ: kacinmanin yonu ise yaramiyor, tek cozum menzil disina
# cikmak. Uc hamlenin ucu de farkli cozum istiyor - ayni cozum ise
# yarasaydi dovus tek tuslu olurdu.
ROTTED_BURST_DAMAGE: Final[int] = 22
ROTTED_BURST_REACH: Final[int] = 46

# Faz 2'nin muhru plakalarla kirilinca boss bu kadar kare savunmasiz.
# `docs/dovus-sistemi.md` zincir penceresi 12 kare; 150 kare ~5 tam
# zincire yetiyor - pencere "kos ve iki vurus at" degil "gercekten
# dov" olmali, yoksa team-up bir angarya gibi hissettirir.
PLATE_STUN_FRAMES: Final[int] = 150


# --- OLUM EKRANI (src/ui/death.py) -------------------------------------------
# Olum vurusunun hitstop'u (12 kare), sarsintisi ve parcaciklari bitsin
# diye bekliyor. Aninda acilirsa oyuncu neyle oldugunu goremiyor.
DEATH_SCREEN_DELAY: Final[int] = 48


# --- ZAMAN KAPILARI (Bolum 13) ------------------------------------------------
# `docs/yapi.md` mekanik 8: *"Kolu cevir, X saniyede kos - **doversek
# degil kacarak**."* Bu son cumle mekanigin tamami: on iki bolumdur
# "once temizle, sonra gec" ogrenen oyuncuya, durmanin CEZALI oldugu
# ilk oda.
#
# Sayac gorunur ama **HUD'da degil**: kapi bir surgu ve zaman gectikce
# asagi iniyor. Yani kalan sure = kalan bosluk yuksekligi (CLAUDE.md 9,
# "diegetik tercih et"). Bir cubuk cizmek hem daha kolay hem daha kotu
# olurdu - oyuncunun gozu koridorda olmali, kosede degil.
#
# Surgu yukaridan indigi icin surenin son diliminde bosluk oyuncunun
# boyundan (2 tile) kisa kaliyor ve gecis fiilen kapaniyor.
# **Kullanilabilir sure nominalin %80'i** - 5 tile'lik surguda gecis
# `progress < 0.80` iken mumkun. (Ilk yorumda %60 yaziyordu; olculunce
# %80 cikti, `tests/test_chapter13.py` bunu her calisisinda dogruluyor.)
#
# Degerler TAHMIN DEGIL, olculdu. Olcut: en yavas karakterin (Ardo,
# 1.8 px/kare) koldan kapiya duz kosu suresi, ve kullanilabilir
# pencerenin ondan **en az 1.35 kat** uzun olmasi. Kalan pay
# hizlanmaya (~8 kare), yoldaki dusmana ve kusursuz olmayan oynayisa.
TIMEGATE_TEACH_FRAMES: Final[int] = 300   # ogretme - 11 tile, pay 2.45x
TIMEGATE_FRAMES: Final[int] = 210         # standart - 9/12 tile, 2.10/1.58x
# Zincir odasi. Sayi en BUYUK ama pencere en DAR - cunku tek sayac iki
# kapiyi birden tasiyor (16 tile). Tile basina dusen sure bolumun en
# azi: 12.5 kare/tile (kol 21.8, okcu 18.7, komutan 14.0). Zorluk
# sayacin kucuklugunden degil **mesafeden** geliyor.
TIMEGATE_CHAIN_FRAMES: Final[int] = 250   # cifte kapi - 16 tile, pay 1.41x
# Son bu kadar karede surgu kirmizi yanip soneriyor. Ses de burada
# degisiyor: iki kanal, cunku renk tek basina yeterli degil
# (CLAUDE.md 10).
TIMEGATE_WARN_FRAMES: Final[int] = 60
# Kolu cevirmek icin bu kadar yakin olmak gerek (piksel). Ayna
# menzili (26) ile ayni: ayni jest, ayni his.
LEVER_REACH: Final[float] = 26.0
# Kol cevrildikten sonra bu kadar kare yeniden cevrilemez. Amac
# yanlislikla iki kez basmayi engellemek - **kilitlemek degil**:
# oyuncu her zaman geri donup yeniden cevirebilmeli (yumusak kilit
# yasak, bkz. DEVIR.md).
LEVER_COOLDOWN: Final[int] = 24
# Surgu kapanirken altinda kalan oyuncu **ezilmiyor**. Ceza olum
# degil kaybedilen zaman: en yakin bosluga itiliyor. Bir zaman
# bulmacasinin cezasi zaman olmali.
TIMEGATE_EJECT_PUSH: Final[float] = 2.2


# --- BOSS 2: Zindanci (Bolum 13) ---------------------------------------------
# `docs/gdd.md` 8 tablosu: *"2 | B13 | Cemo kovalamacasi"*.
# `docs/asset-listesi.md`: *"2 - Zindanci | B13 | 64x80"*.
#
# Curumus Olan (BOSS 1) uc fazinda Katman 1'in uc dusmanini geri
# getiriyordu. Zindanci ayni sinavi Katman 2 icin yapiyor - cunku
# Katman 2 burada BITIYOR:
#
#     Faz 0  GARDIYAN  Kalkanli'nin izi  -> YON     (onden gecilmez)
#     Faz 1  ZINCIR    Mizrakli + Okcu   -> MESAFE + ZAMAN
#     Faz 2  ZINDAN    Komutan'in izi    -> SAYI    (+ karanlik)
GAOLER_HEALTH: Final[int] = 260
GAOLER_POISE: Final[int] = 7             # Katman 2'nin en dayaniklisi
GAOLER_SPEED: Final[float] = 0.34
GAOLER_CONTACT_RANGE: Final[float] = 56.0

# Fenerin isik yaricapi. Arena karanlik; **fener tek guvenilir isik**,
# yani "uzak dur ve tell'i oku" alisildik boss ritmi burada tersine
# doniyor: uzaklik = korluk. Her fazda bir kademe soluyor.
GAOLER_LANTERN_RADIUS: Final[float] = 84.0
GAOLER_LANTERN_DIM: Final[float] = 52.0   # faz 1 - fener catliyor
# Faz 2'de fener kiriliyor: 0. Arena mangallarla aydinlatiliyor.
GAOLER_BRAZIER_COUNT: Final[int] = 3

# Karanlikta bile tell OKUNUR olmali (CLAUDE.md 7: en az 14 kare).
# Cozum gozler: fener sonse de gozleri yaniyor, ve tell sirasinda
# tehlike rengine donuyor. Yani karanlik konumu gizliyor, **niyeti
# degil** - bir boss'un adil olmasi bu ayrimla saglaniyor.
GAOLER_EYE_GLOW: Final[int] = 210

# Hamleler. Her fazin biri ONCEKI bir Katman 2 dusmanini animsatiyor.
GAOLER_SWING_DAMAGE: Final[int] = 14
GAOLER_SWING_REACH: Final[int] = 30
GAOLER_SLAM_DAMAGE: Final[int] = 20
GAOLER_SLAM_REACH: Final[int] = 40
# Zincir: Mizrakli'nin dersi boss olcusunde - senin menzilinin cok
# disindan geliyor (oyuncu kilici ~16).
GAOLER_CHAIN_DAMAGE: Final[int] = 16
GAOLER_CHAIN_REACH: Final[int] = 62
# Anahtar demeti: Okcu'nun dersi. Mermi altyapisi Okcu icin
# yazilmisti (`Hitbox.velocity`) - burada ikinci kez kullaniliyor,
# yani sinir dogru yerdeymis.
GAOLER_KEYS_DAMAGE: Final[int] = 11
GAOLER_KEYS_SPEED: Final[float] = 2.6
GAOLER_KEYS_LIFE: Final[int] = 100
# Cagirma: Komutan'in dersi. Cagirdigi sey **Katman 1** - bu
# zindanda cürüyüp kalmis mahkumlar. Katman 2 muhafiz cagirmak
# daha "askeri" olurdu ama daha az anlamli.
GAOLER_CALL_COUNT: Final[int] = 2
GAOLER_CALL_LIMIT: Final[int] = 6
# Mangali sondurme - faz 2'nin isik ekonomisi. Oyuncu yakiyor, o
# sonduruyor.
#
# **Zincir menzili kadar** (62): sondurme gorunur bir hareket olmali,
# yani boss mangala uzanmali. 40 denendi ve arenada hicbir mangal o
# kadar yakin degildi - hamle her seferinde bosa gidiyordu, yani
# oyuncu bir tell goruyor ve hicbir sey olmuyordu. Bos bir tell,
# olmayan bir tell'den kotudur: oyuncuya sistemi yanlis ogretir.
GAOLER_SNUFF_RANGE: Final[float] = 64.0

# Onden gelen vurus faz 0'da GECMIYOR (Kalkanli'nin dersi). Kalkanli
# gibi "yon" cozumu: arkasina gec. Toparlanma sirasinda gardi dusuyor
# - yani onden de vurulabildigi bir pencere var.
GAOLER_GUARD_PUSHBACK: Final[float] = 2.4


# --- Bolum 13 arenasinin isik ekonomisi --------------------------------------
# Ilk denemede arena OYNANAMAYACAK kadar karanlikti: oyuncunun kendi
# isigi yoktu, yani Zindanci'nin fenerinden uzaktayken kendini bile
# goremiyordu. Ekran goruntusu bunu tek bakista gosterdi.
#
# Cozum bir "parlaklik ayari" degil - iki ISIK KAYNAGI, ikisi de
# diegetik ve ikisi de oyunun var olan dilinden:
#
#   * Kolye. `CLAUDE.md` 9 zaten *"kolye pusulasi boyundaki sprite
#     parildamasiyla anlatilir"* diyor. Burada o parilti bir isik
#     oluyor: kendini ve kilic menzilini goruyorsun, **boss'u degil**.
#     Yani karanlik hala bir soru; yalnizca haksiz degil.
#   * Zindanci'nin gozleri. Fener kirildiktan sonra govdesi kayboluyor
#     ama gozleri karanligi deliyor - ve tell sirasinda buyuyor.
#     `CLAUDE.md` 7 baglayici: her saldiri 14 kare onceden okunabilir.
#     Karanlik konumu gizler, NIYETI degil.
NECKLACE_LIGHT_RADIUS: Final[float] = 34.0
# Gozler bostayken kucuk bir leke, tell'de iki kati - buyume "geliyor"
# demenin isik tarafindaki karsiligi.
GAOLER_EYE_LIGHT_RADIUS: Final[float] = 20.0
GAOLER_EYE_TELL_RADIUS: Final[float] = 44.0


# --- ARDO'NUN DUZENEGI (Bolum 12) --------------------------------------------
# `docs/gdd.md` 9 mekanik havuzuna **11. madde**: sürülebilir düzenek.
# Arda 30.08.2026'da onayladi (soru: *"jetpack, helikopter, araba veya
# tank gibi surulebilir bisey"*). Dordu de reddedildi - teknoloji cagi
# tutmuyor, zindanda mesale ve zincir var. Yerine dunyanin kendi
# aracı: Ardo'nun kuyuya kurdugu karsi agirlikli iniş kafesi.
#
# ## Nefes bolumune araç KOYMAK onu bozmaz, tasir
#
# B12'nin isi `docs/gdd.md` 156: *"Ozlem - yoklugunda birakilmis
# izler."* Bir araç normalde bunu bozardi (hizli gecersin, izleri
# kacirirsin) - ama araç ONUN yaptigi bir sey oldugu icin binmek
# zaten yakinlik. `docs/yapi.md` B12 kamp kalintilarindan ve
# "senin icin birakilmis erzak"tan bahsediyor; duzenek de o
# birakilanlardan biri.
#
# ## Mekanik: inersin, YAVASLAMAYI secersin
#
# Kafes kendi iniyor. Tek kontrol fren. Duvarlarda Ardo'nun
# isaretleri var ve yalnizca **yavasken** okunuyor. Ceza yok, olum
# yok, basarisizlik yok - degisen tek sey onun ne kadarini gordugun.
# Bir nefes boluműnün puani beceri degil **yakinlik** olmali.
#
# Gerilim tek bir kuraldan geliyor: **yukari cikilmiyor.** Gectigin
# isaret bir daha gelmiyor. Sifir kod, ve oyunun butun cumlesi.
RIG_FALL_SPEED: Final[float] = 1.15       # serbest inis (piksel/kare)
# Fren hizi **olculdu**, secilmedi. 0.22 ilk denemeydi ve tam frenli
# bir inis 66 saniye suruyordu - bir nefes bolumu sabir sinavi degil.
# Olcut: dikkatli oyuncu ile aceleci oyuncu arasindaki fark anlamli
# olsun ama uzun olan sikici olmasin.
#
#     fren   serbest   tam frenli   gercekci (yalniz isaretlerde)
#     0.22    13.0sn      66.7sn        51.3sn   <- sabir sinavi
#     0.35    13.0sn      42.0sn        34.1sn
#     0.45    13.0sn      32.7sn        27.5sn   <- SECILEN
#
# Ust sinir `MARK_READ_SPEED` (0.55): frenli halde isaretler MUTLAKA
# okunabilmeli, yoksa mekanik kendi kendine yalan soyler.
RIG_BRAKE_SPEED: Final[float] = 0.45      # fren basiliyken
# Hizlanma/yavaslama yumusak olmali: ani duran bir kafes asansor
# degil tuzak gibi hissettiriyordu.
RIG_ACCEL: Final[float] = 0.045
# Kafesin genisligi (tile). Oyuncu ustunde saga sola yuruyebiliyor -
# isaretler iki duvarda da oldugu icin bu bir SECIM: hangi tarafa
# bakiyorsun.
RIG_WIDTH_TILES: Final[int] = 5
# Bir isaret bu kadar yakinken ve kafes bu hizin altindayken okunuyor.
MARK_READ_RANGE: Final[float] = 30.0
MARK_READ_SPEED: Final[float] = 0.55


# --- YANKI'NIN TERSINE DONMESI (Bolum 14'ten sonra KALICI) -------------------
# `docs/yapi.md` B14: *"Rey anlar: Yanki lanet degil, asagidaki seyin
# sesi. Hep yardim ediyordu cunku onu cagiriyordu."*
# *Mekanik:* **Yanki tersine doner - actiginda dusmanlar da seni gorur.**
#
# On uc bolumdur refleks suydu: emin degilsen Yanki'yi ac. Bu bolumden
# sonra ayni tus seni ELE VERIYOR. Arac degismedi, **sozlesme degisti** -
# ve bu, bir sayiyi buyutmekten cok daha keskin bir zorluk artisi.
#
# Bayrak `SaveData.flags["sense_betrayed"]`de duruyor ve `PlayScene`
# okuyor, yani B15-B18 hicbir sey yazmadan devraliyor. "Her bolum bir
# satir eklemek zorunda" bu projede uc kez hatanin sekli oldu
# (kilic verme, boss bari, yetenek geri yukleme).
#
# Ardo'da ayni kural, baska kurgu: Iz Surme'yi acmak da ele veriyor.
# Onun twist'i "sesler benim degil" degil, **"izler benim icin
# birakilmis"** - ayni cumle, onun dilinde.
SENSE_BETRAYAL_RANGE: Final[float] = 240.0
# Duyu acildiktan bu kadar kare sonra uyanma basliyor. Anlik olsaydi
# yanlislikla dokunan oyuncu cezalandirilirdi; bu pencere "acik
# tutmak" ile "bir an bakmak" arasindaki farki koruyor.
SENSE_BETRAYAL_DELAY: Final[int] = 24


# --- BOSS 3: Kaynak (Bolum 14) -----------------------------------------------
# `docs/gdd.md` 8: *"3 | B14 | Yanki'nin kaynagi"*.
# `docs/asset-listesi.md`: *"3 - Yanki Kaynagi | B14 | 96x96"* - oyunun
# en buyuk sprite'i.
#
# Curumus Olan Katman 1'in sinaviydi, Zindanci Katman 2'nin. Kaynak
# Katman 3'un **atasi**: uc fazi Yanki'nin Cocuklari'nin uc ihanetini
# tasiyor, cunku onlar zaten onun cocuklari.
#
#     Faz 0  SESSIZ'in izi      Yanki onu GOSTERMIYOR
#     Faz 1  YANKILAYAN'in izi  sahte suretler cikariyor
#     Faz 2  BOLUNEN'in izi     gercekten bolunuyor
SOURCE_HEALTH: Final[int] = 300
SOURCE_POISE: Final[int] = 8
SOURCE_SPEED: Final[float] = 0.28
SOURCE_CONTACT_RANGE: Final[float] = 70.0

# Feryat: yonsuz ses dalgasi. Kacinmayla degil **uzaklasarak** gecilir -
# Curumus Olan'in radyal patlamasiyla ayni ders, boss olcusunde.
SOURCE_WAIL_DAMAGE: Final[int] = 18
SOURCE_WAIL_REACH: Final[int] = 58
# Uzanma: uzun kol. Mizrakli'nin dersi degil - bu bir SES, duvardan
# geciyor. Menzil uzun ama tell de uzun.
SOURCE_REACH_DAMAGE: Final[int] = 15
SOURCE_REACH_LENGTH: Final[int] = 74
SOURCE_CRUSH_DAMAGE: Final[int] = 24
SOURCE_CRUSH_REACH: Final[int] = 46

# Sahte suretler. **Yanki onlari GOSTERIYOR, gercegini gostermiyor** -
# bolumun tezi tek satirda: arac bozuk degil, SENIN DEGIL.
SOURCE_MIMIC_COUNT: Final[int] = 2
SOURCE_MIMIC_HEALTH: Final[int] = 1        # tek vurusla dagiliyor
SOURCE_MIMIC_LIFE: Final[int] = 300        # kendiliginden de soluyor
SOURCE_MIMIC_RANGE: Final[float] = 90.0
# Faz 2'de gercekten bolunuyor: cagirdiklari Yankilayan - kendi
# cocuklari.
SOURCE_SPLIT_COUNT: Final[int] = 2
SOURCE_SPLIT_LIMIT: Final[int] = 4


# --- SESSIZLIK / GURULTU (Bolum 15) ------------------------------------------
# `docs/yapi.md` mekanik 9: *"Yanki kapali oynama; ses cikarirsan suru
# uyanir."* Ve uygulama notu **yontemi de veriyor**: *"dusmanlara
# `alert_level` float'i ekle, gurultu olaylariyla artir/azalt. Var olan
# AI'ya eklenti, yeni sistem degil."* Aynen oyle yapildi.
#
# ## Bolum 14 bunu zaten kurdu
#
# B14'ten sonra duyuyu acmak dusmanlari uyandiriyor
# (`sense_betrayed`). B15 *"Yanki'yi kapali oynamak zorundasin"*
# diyor - yani bu bolum yeni bir kisit getirmiyor, bir onceki
# bolumun sonucunu **oynatiyor**. Iki bolum tek bir yay.
#
# ## Sayilar bir CUMLE kuruyor
#
#     yurumek     duyulmuyor denecek kadar az   -> her zaman guvenli
#     kosmak      birkac adimda uyandirir       -> acele bedelli
#     inis/vurus  aninda uyandirir              -> dovus = basarisizlik
#
# Ucu birden `docs/yapi.md`nin *"kosarsan uyanirlar"* cumlesini
# sayiya ceviriyor.
NOISE_WALK: Final[float] = 0.06
# 0.30 idi ve **kosmak hicbirini uyandirmiyordu** - yani belgenin
# "kosarsan uyanirlar" cumlesi kodda karsiliksizdi. Sebep aritmetikti:
#
# Adim sesi mesafeye bagli (~50 pikselde bir), yani duyulma
# bolgesinden (300 px cap) gecerken her hizda ~6 adim atiliyor. Ama
# **gecis suresi** hiza bagli: kosarken 150 kare, yururken 500.
# Sonme kare basina isledigi icin yavas gecen daha cok soluyor - ve
# 0.30 ile hizli gecen de esige varamiyordu.
#
# Deger **olculdu**, hesaplanmadi. Ilk tahmin 0.60 idi ve tutmadi:
# adim sesinin ~50 pikselde bir geldigini varsaymistim, gercekte
# ~87 pikselde bir geliyor. Yani duyulma bolgesinden (300 px cap)
# gecerken yalnizca **uc** kullanilabilir adim var, alti degil.
#
# Olculen gecis (kosu, tek uyuyan):
#
#     mesafe 122 -> +0.11
#     mesafe  25 -> +0.50      zirve 0.687, esik 1.0 - UYANMIYOR
#     mesafe  72 -> +0.31
#
# 0.90'da ayni gecis 1.0'i asiyor: en yakin adim tek basina 0.75,
# ikincisi esigi geciriyor. Yani **kosmak iki adimda uyandiriyor.**
#
# Yuruyus hala imkansiz: 0.06 x 0.83 = 0.05 kazanc, adimlar arasi
# 145 kare ve o surede sonme 0.72. Pay devasa - yanlislikla bir kare
# kosan oyuncu cezalandirilmiyor.
NOISE_RUN: Final[float] = 0.90
NOISE_LAND: Final[float] = 0.85
NOISE_ATTACK: Final[float] = 1.20      # tek vurus yeter - dovus cozum degil
NOISE_DODGE: Final[float] = 0.34
# Dunyadaki dikkat dagitici (can, gevsek tas). Oyuncudan UZAKTA
# calindigi icin degeri yuksek olmali, yoksa suru yerinden kalkmaz.
NOISE_CHIME: Final[float] = 1.50

# Gurultunun duyuldugu yaricap (piksel). Uzaklikla dogrusal soluyor.
NOISE_RANGE: Final[float] = 150.0
# Uyaniklik her karede bu kadar soluyor.
#
# 0.010 idi ve iki isi birden bozuyordu: hem kosmayi duyulmaz
# yapiyordu (bkz. `NOISE_RUN`), hem de "kimildanma" esigi ekranda
# neredeyse hic gorunmuyordu - oyuncu yaklastigini fark etmeden
# uyandiriyordu.
#
# 0.005 -> tam dolu bir uyaniklik ~3.3 saniyede sifirlaniyor. Hata
# yapan oyuncu hala **bekleyerek** duzeltebiliyor (affetmeyen bir
# gizlilik bolumu kaydet-yukle oyununa doner) ama bekleme artik
# gorulebilecek kadar uzun.
ALERT_DECAY: Final[float] = 0.005
# Bu esigin ustunde dusman uyaniyor ve bir daha uyumuyor.
ALERT_WAKE: Final[float] = 1.0
# Bu esigin ustunde henuz uyanmadi ama **kimildaniyor** - oyuncu
# uyariyi gormeli. Sessiz bir esik oyuncuya haksiz gelir.
ALERT_STIR: Final[float] = 0.45
# Uyuyan dusmanin siluet deformasyonu (genislik, yukseklik).
# `Enemy.silhouette_scale` bunu uyaniklikla (1.0, 1.0)'a dogru
# yumusatiyor, yani uyanmakta olan dusman **dogruluyor.**
#
# Uc deger render edilip **bakildi** (`build/testshots/b15_squash_*`):
#
#   0.85  22 px -> 19 px. Dik durandan ayirt edilemiyor; ekranda fark
#         secilmiyor, yani hicbir sey anlatmiyor.
#   0.72  22 px -> 16 px. Rey'in yanindayken belirgin kisa - cokmus
#         bir siluet, ama bacaklar hala okunuyor. ★
#   0.55  22 px -> 12 px. Bacaklar kayboluyor, siluet okunmaz bir
#         kutuge donuyor ve govde diyalog kutusunun arkasinda kaliyor.
SLEEP_SQUASH: Final[tuple[float, float]] = (1.12, 0.72)
# Sesin geldigi yere bu kadar yaklasinca arastirma bitiyor.
INVESTIGATE_REACH: Final[float] = 20.0
# Arastirma en fazla bu kadar surer, sonra dusman yerine doner.
INVESTIGATE_FRAMES: Final[int] = 260


# Rezonans darbesinin **kendi** gurultusu (Bolum 15).
#
# Darbe bedava olmamali: oyuncu bir cani uzaktan calarken kendi sesini
# de cikariyor. Bu tek sayi bolumun bulmacasini kuruyor - **yeterince
# uzak dur ki kendi darbeni duymasinlar, yeterince yakin dur ki cana
# ulassin.** Sifir olsaydi dikkat dagitmak risksiz bir dugme olurdu.
#
# Kosmaktan (0.30) az, yurumekten (0.06) cok: acele etmekten sessiz,
# yurumekten gurultulu.
NOISE_RESONATE: Final[float] = 0.18
