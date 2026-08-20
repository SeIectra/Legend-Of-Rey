---
name: lore-dev
description: LORE - Legend of Rey Echoes oyununu calistir, test et ve gorsel olarak dogrula. Oynanis, sprite, bolum, savas ya da fizik degisikliklerinden sonra kullan. "oyunu calistir", "test et", "sprite'lara bak", "bolum ekle", "hissi ayarla" gibi isteklerde devreye girer.
---

# LORE gelistirme dongusu

Bu depo pygame-ce ile yazilmis bir 2D platformer. Degisiklikleri **gormeden**
tamamlanmis sayma: oyun basssiz calistirilabiliyor ve ekran goruntusu
uretebiliyor, bu yuzden her degisiklik gorsel olarak dogrulanabilir.

## Python

Sanal ortam depo kokunde: `.venv/`. Sistem Python'u kullanma.

```
Windows : .venv\Scripts\python.exe
Diger   : .venv/bin/python
```

Yoksa kur:
```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## Dogrulama sirasi

Oynanisa dokunan her degisiklikten sonra, bu sirayla:

1. **Duman testi** - oyun aciliyor, menuler geziliyor, bolum yukleniyor mu?
   ```
   .venv/Scripts/python tools/smoke_test.py
   ```
   `build/testshots/shot_*.png` uretir. En az `shot_04_play.png` dosyasini
   Read ile ac ve **gercekten bak** - cokme yoksa da gorsel bozulmus olabilir.

2. **Savas testi** - hasar, olum, Essence dusmesi, dusman AI, dikenler.
   ```
   .venv/Scripts/python tools/combat_test.py
   ```

3. **Sprite'a dokunulduysa** - kontakt sayfasi bas ve incele.
   ```
   .venv/Scripts/python tools/sprite_sheet.py
   ```
   Tek animasyonu buyuk gormek icin ortam degiskenleriyle daralt:
   `ONLY=rey_armed STATES=attack1,attack2` (varsayilan: hepsi, cok uzun olur).
   Ozellikle **silahin hucre disina tasip kirpilmadigini** kontrol et.

4. **Bolum degistiyse** - yeniden uret ve dogrula.
   ```
   .venv/Scripts/python tools/make_levels.py
   ```
   `OK` disinda bir satir varsa bolum oynanamaz durumda; duzeltmeden birakma.
   `lore/data/levels/*.json` dosyalarini elle duzenleme - bu arac uretir.

## Gercek pencerede calistirma

```
.venv/Scripts/python run.py
```
Kullanici oynayacaksa bunu oner; sen kendi dogrulamani basssiz testlerle yap
(pencere acan bir surec oturumu bloke eder).

## Sik karsilasilan tuzaklar

- **`convert()` / `convert_alpha()` cagrisi `display.set_mode()` oncesinde
  yapilamaz.** `App.__init__` icinde pencere once acilir.
- **`dt == 0` gelebilir** (hitstop sirasinda). Bolme yapmadan once kontrol et.
- **`BLEND_RGB_ADD` alfayi yok sayar.** Siddeti `set_alpha` ile degil, renkleri
  `BLEND_RGB_MULT` ile kisarak ayarla.
- **Sprite hucresi silahi icermeli.** Kilic/tirpan animasyon boyunca hucreden
  tasarsa sessizce kirpilir; `tools/sprite_sheet.py` cerceve cizerek gosterir.
- **Ziplama mesafesi 4 tile.** `RUN_SPEED` veya `JUMP_SPEED` degistiyse
  `Level.MAX_JUMP_TILES` degerini de guncelle, sonra `make_levels.py` calistir.

## Mimari

Detay icin `CLAUDE.md`, plan icin `docs/ROADMAP.md`.
