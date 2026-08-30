"""Team-up firlatma - yoldas seni yukari atiyor.

`docs/yapi.md` mekanik havuzu 6: *"Ardo seni yukari firlatir / **sen ona
basamak olursun**."* B9'da ogreniliyor.

`docs/yapi.md` 118 uygulama notu **acikca** soyluyor:

    "Team-up firlatma: tek seferlik impulse + animasyon state. Fizik
     motoru gerekmez."

Bu modul o cumleden fazlasini yapmiyor. Bir yay sistemi, bir egri
cozucu, bir hedef tahmini yok: iki karakter yan yana ve yerdeyken tusa
basiliyor, atilan kisiye tek bir dikey hiz veriliyor. Gerisini zaten var
olan yer cekimi hallediyor.

## Cift yonlu ve bu onemli

`docs/gdd.md` 155 romantik yay: *"B9 | Guven | Firlatma - kendini ona
birakiyorsun."* An oyuncunun **kontrolu birakmasi** uzerine kurulu.

Ama belge "sen ona basamak olursun" da diyor. Yani her iki taraf da
atan olabiliyor: Rey hafif, Ardo guclu - Ardo Rey'i daha yukari
atiyor. Sayi karakterden turuyor, roller sabit degil.

## Neden bir "sistem"

Tek bir fonksiyon olabilirdi ama uc sey durum tutuyor: hazirlik
penceresi (iki taraf da yerde ve yakin olmali), bekleme (arka arkaya
firlatma zincirlemesin) ve son firlatmanin karesi (animasyon ve ses
icin). Bunlari sahneye dagitmak bes bolumde bes kopya demekti.
"""
from __future__ import annotations

from src.config import PLAYER_JUMP_SPEED

# Firlatma **ziplamanin bu kati**. 1.85 = ~13 tile yukseklik: normal
# ziplama 3.8 tile, yani firlatma ulasilamayan yerleri aciyor ama
# sinirsiz degil - kule hala kat kat tirmaniliyor.
BOOST_MULTIPLIER = 1.85

# Guclu olan daha yukari atiyor. Ardo Rey'i bu kadar fazla atiyor;
# tersi (Rey Ardo'yu) tam tersi carpanla. Ikisi de calisiyor, ikisi de
# ayni degil - `docs/yapi.md` 18: "sen ona basamak olursun".
STRONG_BONUS = 1.15
LIGHT_PENALTY = 0.86

# Iki taraf da bu mesafeden yakin olmali (piksel). Genis olsaydi
# oyuncu yoldasi gormeden ekranin obur ucundan firlatilirdi.
BOOST_RANGE = 26.0

# Iki firlatma arasi bekleme (kare). Olmasaydi tus basili tutulup
# zincirleme firlatma yapilir ve kule dikey bir asansor olurdu.
BOOST_COOLDOWN = 42

# Firlatma animasyonu/sesi bu kadar kare sonra biter.
BOOST_FRAMES = 14


class BoostState:
    """Firlatma hazirligi ve beklemesi."""

    __slots__ = ("cooldown", "frames", "unlocked", "count")

    def __init__(self, unlocked: bool = False) -> None:
        # B9'da ogreniliyor; oncesinde tus hicbir sey yapmiyor.
        self.unlocked = unlocked
        self.cooldown = 0
        self.frames = 0
        self.count = 0          # toplam - ogretici bunu sayiyor

    @property
    def active(self) -> bool:
        return self.frames > 0

    def update(self) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.frames > 0:
            self.frames -= 1

    def ready(self, thrower, rider) -> bool:
        """Firlatma su an mumkun mu?

        Uc sart ve ucu de oynanistan geliyor:
          * **ikisi de yerde** - havada firlatmak ikinci bir ziplama
            olurdu ve cift ziplama ayri bir yetenek
          * **yakin** - goremedigin birine kendini birakamazsin
          * **bekleme dolmus** - zincirleme yok
        """
        if not self.unlocked or self.cooldown > 0 or self.active:
            return False
        if thrower is None or rider is None:
            return False
        if not thrower.body.grounded or not rider.body.grounded:
            return False
        return abs(thrower.body.center_x - rider.body.center_x) <= BOOST_RANGE

    def launch(self, thrower, rider, strong: bool) -> bool:
        """Tek seferlik impuls. Basarili olduysa True.

        `strong` atan tarafin guclu olani (Ardo) olup olmadigi.
        """
        if not self.ready(thrower, rider):
            return False
        speed = PLAYER_JUMP_SPEED * BOOST_MULTIPLIER
        speed *= STRONG_BONUS if strong else LIGHT_PENALTY
        rider.body.vy = -speed
        rider.body.grounded = False
        # Atan taraf hafifce cokuyor - kuvvetin bir karsiligi olmali.
        thrower.body.vx = 0.0
        self.frames = BOOST_FRAMES
        self.cooldown = BOOST_COOLDOWN
        self.count += 1
        return True


# Ogretici ipucu bu kadar firlatmadan sonra bir daha gosterilmiyor.
HINT_AFTER = 1
