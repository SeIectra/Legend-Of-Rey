"""IZ SURME - Ardo'nun karsi mekanigi.

`docs/derinlestirme.md` 2.4 (★★), bu projenin en net tasarim tespiti:

    "Su an Ardo'nun oynanisi 'Yanki yok' - yani bir EKSIKLIKLE tanimli.
    Bu zayif tasarim. Ona kendi guclu mekanigini ver."

    "IZ SURME: Ardo gecmisi okur. Bir yere baktiginda orada olan seyin
    izini gorur. (...) Rey GELECEGI/GIZLIYI duyar (ses = uzamsal), Ardo
    GECMISI gorur (iz = zamansal). Ikisi ayni zindani iki farkli boyuttan
    okur. Ayni bolum, iki farkli oyun."

## Ayni tus, zit bilgi

Rey'de `Action.ECHO` Yanki'yi aciyor, Ardo'da Iz Surme'yi. **Ayni egri**
(`RISE_FRAMES`/`FALL_FRAMES`) kullaniliyor: acilirken hizli, kapanirken
yavas. Iki karakterin girdisi ayni HISSETMELI - ayrilan sey duyu, tempo
degil. Ayri bir egri yazsaydik iki karakter "farkli oyunlar" degil
"farkli kalitede oyunlar" gibi okunurdu.

## Bedel: gecmis, simdiyi orter

Yanki'nin bedeli ekranin kararmasi ve savunmanin dusmesi. Iz Surme'nin
bedeli daha ince ama ayni agirlikta: **yasayan dusmanlar soluyor.** Ardo
gecmise bakarken simdiyi net goremiyor. Tematik olarak dogru (adam
oluleri okuyor) ve mekanik olarak gercek bir risk - dovus ortasinda
acmak kotu fikir.

Bu, `TRACKING_ENEMY_FADE` ile olculuyor; savunma DUSMUYOR. Iki karakterin
bedeli ayni kanaldan gelseydi mekanikler ayni sey olurdu.

## Izler nereden geliyor - icerik YAZMADAN

Kritik kisit: `CLAUDE.md` 3, sirasi gelmemis bolum icerigi yazilmaz. Yani
her bolume elle "Cemo buradan gecti" izleri koyamayiz.

Cozum yapisal: **Yanki neyi acikliyorsa Iz Surme de onu acikliyor.**
Kirilabilir duvarlar Ardo'da da parliyor - ama gerekce farkli: Rey
duvarin ARKASINI duyuyor, Ardo duvardan birinin GECTIGINI goruyor. Ayni
bilgi, iki farkli hikaye. Bolum verisine tek satir eklemeden esitlik
saglaniyor.

Ustune dunyanin **kendi urettigi** izler biniyor:
  * dusmanlarin ve oyuncunun ayak izleri (`record_step`)
  * dovusun biraktigi kan/patlama izleri (`DecalField` ile ayni anlar)

Yani Ardo'nun ekrani oyun oynandikca doluyor. Bos bir koridorda az sey
var; bir dovusun gectigi koridorda cok. Bu tam olarak "gecmisi okumak".
"""
from __future__ import annotations

from src.config import (
    TRACE_FADE_FRAMES, TRACE_MAX, TRACKING_ENEMY_FADE, TRACKING_FALL_FRAMES,
    TRACKING_RANGE, TRACKING_RISE_FRAMES, TRACKING_STEP_FRAMES,
)

# Iz turleri. Duz dize - `Enum` uc deger icin fazla agir olurdu ve bu
# degerler cizim tarafinda dogrudan renk zincirine esleniyor.
FOOT = "foot"        # biri gecti
BLOOD = "blood"      # biri yaralandi
SCORCH = "scorch"    # bir sey patladi


class Trace:
    """Tek bir iz. Konum, tur, ve **ne zaman** birakildigi."""

    __slots__ = ("x", "y", "kind", "facing", "frame")

    def __init__(self, x: float, y: float, kind: str, facing: int,
                 frame: int) -> None:
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.facing = facing
        self.frame = frame

    def age(self, now: int) -> float:
        """0 = taze, 1 = tamamen soluk. Yasi GORSEL, izler silinmiyor.

        `docs/derinlestirme.md`: *"ayak izleri kimin, NE ZAMAN gectigini
        gosterir"*. Yasin okunabilmesi bilginin yarisi - taze bir iz
        "az once buradaydi", soluk bir iz "cok once".
        """
        if TRACE_FADE_FRAMES <= 0:
            return 0.0
        return min(1.0, max(0, now - self.frame) / TRACE_FADE_FRAMES)


class TraceField:
    """Bir bolumun izleri. Sahne basina bir tane.

    `DecalField`'in kardesi ama isi farkli: lekeler **cizilmis piksel**,
    izler **sorgulanabilir veri**. Lekeler tek bir yuzeye pisiriliyor ve
    geri okunamiyor; Iz Surme'nin "yakindakileri goster, yasina gore
    soldur" isi icin konumlarin durmasi gerek.
    """

    def __init__(self) -> None:
        self.traces: list[Trace] = []
        self.frame = 0
        # Aktor basina son adim karesi - her karede iz birakmasin diye.
        self._last_step: dict[int, int] = {}

    def update(self) -> None:
        self.frame += 1

    def clear(self) -> None:
        self.traces.clear()
        self._last_step.clear()
        self.frame = 0

    # --- Ekleme -------------------------------------------------------------
    def add(self, x: float, y: float, kind: str = FOOT,
            facing: int = 1) -> None:
        """Iz birakir. Ust sinir asilinca **en eskisi** dusuyor.

        Kare butcesi: 400 iz her karede tek tek cizilseydi pahali olurdu,
        ama yalnizca Iz Surme acikken ve yalnizca menzildekiler ciziliyor.
        """
        self.traces.append(Trace(x, y, kind, facing, self.frame))
        if len(self.traces) > TRACE_MAX:
            del self.traces[:len(self.traces) - TRACE_MAX]

    def record_step(self, actor, kind: str = FOOT) -> None:
        """Yuruyen bir aktorun ayak izi.

        Her karede degil `TRACE_STEP_FRAMES`'te bir: her karede iz birakmak
        hem listeyi doldurur hem de "iz" degil "cizgi" cizerdi. Yalnizca
        **yerdeyken ve hareket ederken** - havada ayak izi olmaz.
        """
        body = getattr(actor, "body", None)
        if body is None or not body.grounded or abs(body.vx) < 0.15:
            return
        key = id(actor)
        if self.frame - self._last_step.get(key, -10_000) < TRACKING_STEP_FRAMES:
            return
        self._last_step[key] = self.frame
        self.add(body.center_x, body.bottom, FOOT,
                 getattr(actor, "facing", 1))

    # --- Sorgu --------------------------------------------------------------
    def near(self, x: float, y: float, radius: float) -> list[Trace]:
        """Menzildeki izler. Kare mesafe - karekok gereksiz."""
        limit = radius * radius
        return [t for t in self.traces
                if (t.x - x) ** 2 + (t.y - y) ** 2 <= limit]


class TrackingState:
    """Ardo'nun Iz Surme durumu. Rey'de hic olusturulmaz.

    `EchoState` ile ayni desen: `holding` girer, `strength` egrisi cikar.
    Kod her yerde "hangi karakter?" diye dallanmiyor, `is None` diye
    soruyor.
    """

    __slots__ = ("holding", "strength")

    def __init__(self) -> None:
        self.holding = False
        self.strength = 0.0

    @property
    def active(self) -> bool:
        return self.strength > 0.01

    @property
    def range(self) -> float:
        """Su anki okuma menzili - egri ile olcekleniyor."""
        return TRACKING_RANGE * self.strength

    @property
    def enemy_fade(self) -> float:
        """Yasayan dusmanlarin solma orani 0..1 - **bedel**.

        Ardo gecmise bakarken simdiyi net goremiyor. Yanki'nin karartmasi
        ne ise bu odur; ama savunmaya dokunmuyor - iki karakterin bedeli
        ayni kanaldan gelseydi mekanikler ayni sey olurdu.
        """
        return TRACKING_ENEMY_FADE * self.strength

    def update(self, holding: bool) -> None:
        self.holding = bool(holding)
        step = (1.0 / TRACKING_RISE_FRAMES if self.holding
                else -1.0 / TRACKING_FALL_FRAMES)
        self.strength = max(0.0, min(1.0, self.strength + step))
