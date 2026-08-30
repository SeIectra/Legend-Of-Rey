"""Yanki Sadakati - **gorunmez** sayac.

`docs/derinlestirme.md` 2.2 bunu bastan tarif ediyor:

    Oyuncunun Yanki'ya ne kadar guvendigini takip eden gorunmez bir
    deger.
      * Yanki'nin gosterdigi yoldan gidersen: sadakat artar
      * Yanki'yi gormezden gelip kendi yolunu bulursan: azalir

    Etkisi: Bolum 14'teki twist sahnesi sadakat degerine gore farkli
    oynanir. Cok guvendiysen ihanet daha aci; hic guvenmediysen
    "biliyordum" ani. Ayni sahne, iki farkli duygu.

    Ucuz mu? Evet - tek bir int, iki farkli ara sahne varyanti.

Bu modul o "tek int". B10'da (Yanki'nin ilk yalani) yazilmaya
basliyor, B14'te okunacak.

## Oyuncuya ASLA gosterilmiyor

HUD'da bar yok, menude sayi yok, bildirim yok. Gorunur olsaydi oyuncu
onu **optimize** ederdi ve olculen sey guven degil puan olurdu.

`docs/gdd.md` 11'in dili: bir sey ya jestle ya mekanikle anlatilir.
Sadakat ucuncu bir yol: **hic anlatilmaz**, yalnizca sonucu yasanir.

## Neden kayitta ve neden sinirli

Kayitta cunku bolumler arasi tasiniyor - B10'daki secim B14'te
okunuyor. Sinirli (`MIN`..`MAX`) cunku sinirsiz bir sayac tek bir
bolumde uc basina dayanip geri kalan sekiz bolumu anlamsizlastirirdi.
"""
from __future__ import annotations

# Sayacin sinirlari. Dar aralik bilincli: on iki-on bes karar noktasi
# var ve her biri gercekten agirlik tasimali.
MIN = -6
MAX = 6

# Baslangic **sifir**: Rey Yanki'ya ne guveniyor ne guvenmiyor. Oyunun
# ilk bolumlerinde onu tanimiyor bile.
START = 0

SETTINGS_KEY = "echo_loyalty"


def read(save_data) -> int:
    """Kayittaki sadakat. Kayit yoksa notr."""
    if save_data is None:
        return START
    value = save_data.flags.get(SETTINGS_KEY, START)
    try:
        return max(MIN, min(MAX, int(value)))
    except (TypeError, ValueError):
        return START


def _write(save_data, value: int) -> int:
    if save_data is None:
        return START
    clamped = max(MIN, min(MAX, value))
    save_data.flags[SETTINGS_KEY] = clamped
    return clamped


def followed(save_data, weight: int = 1) -> int:
    """Oyuncu Yanki'nin dedigini yapti."""
    return _write(save_data, read(save_data) + weight)


def ignored(save_data, weight: int = 1) -> int:
    """Oyuncu Yanki'yi dinlemedi, kendi yolunu buldu."""
    return _write(save_data, read(save_data) - weight)


def trusts(save_data) -> bool:
    """B14'un soracagi soru: bu oyuncu Yanki'ya guveniyor mu?"""
    return read(save_data) > 0


def band(save_data) -> str:
    """Sadakatin adi - ara sahne varyantini secmek icin.

    Uc kova yeter (`docs/derinlestirme.md` 2.2 iki varyanttan
    bahsediyor; ortadaki "kararsiz" oyuncuyu ikisinden birine zorlamak
    yerine kendi tonunu aliyor).
    """
    value = read(save_data)
    if value >= 3:
        return "trusting"
    if value <= -3:
        return "wary"
    return "uncertain"
