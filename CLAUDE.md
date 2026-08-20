# LORE — Legend of Rey: Echoes

2D yandan kaydırmalı aksiyon-platformer. Python 3.13 + pygame-ce.
İlham: Samsung tuşlu telefonlardaki *Forgotten Warrior* (2004, J2ME).

## Çalıştırma

```bash
.venv/Scripts/python run.py          # Windows
.venv/bin/python run.py              # Linux/macOS
```

Oyun içi: `F3` hata ayıklama katmanı · `F11` tam ekran · `F12` ekran görüntüsü · `Esc` duraklat

## Araçlar

```bash
python tools/make_levels.py     # Bölümleri tasarla, doğrula ve JSON'a yaz
python tools/smoke_test.py      # Başsız uçtan uca test (menü → oyun → duraklat)
python tools/combat_test.py     # Savaş sistemlerini doğrula (hasar, ölüm, AI)
python tools/sprite_sheet.py    # Tüm sprite'ları kontakt sayfası olarak bas
```

Testler `SDL_VIDEODRIVER=dummy` ile pencere açmadan çalışır ve
`build/testshots/` altına ekran görüntüsü bırakır. **Oynanışı etkileyen bir
değişiklikten sonra ikisini de çalıştır.**

## Mimari

```
lore/
├── constants.py   Sanal çözünürlük, zaman adımı, tile boyutu, katman sırası
├── core/          app · scene · input · assets · audio · config · save · camera · mathx
├── gfx/           palette · forge · sprites · tiles · particles · lighting · postfx · text · ui
├── world/         tilemap · level · parallax
├── entities/      entity · player · enemies · projectile · pickups
├── systems/       physics · combat
├── scenes/        boot · title · play · pause · settings
└── data/levels/   *.json  (tools/make_levels.py üretir — elle düzenleme)
```

### Değiştirmeden önce bilmen gerekenler

**Sanal çözünürlük 480×270.** Her şey buna çizilir, sonra tam sayı katıyla
büyütülür. Piksel koordinatları daima tam sayıya yuvarlanmalı; alt-piksel
konumlar pixel art'ta titreme yaratır.

**Sabit zaman adımı 1/60.** `App._tick` fiziği sabit adımlarla sürer. Hiçbir
yerde `dt`'siz sabit hız yazma. `dt == 0` gelebilir (hitstop sırasında) —
sıfıra bölme kontrolü gerekir.

**Renkle değil, palet indeksiyle çizilir.** `gfx/forge.py` içindeki `Canvas`
her piksel için (rampa, basamak) tutar; `shade()` ve `outline()` bunun üstünde
çalışır, `resolve()` gerçek renge çevirir. Yeni sprite eklerken doğrudan RGB
yazma — palet tutarlılığı buradan geliyor.

**Hasar tek yerden geçer.** Saldıran taraf `scene.combat.attack(...)` ile
kısa ömürlü bir `Hitbox` yaratır; `CombatSystem` çözer, `PlayScene.on_hit`
hitstop/sarsıntı/partikül/sesi verir. Doğrudan `target.take_damage()` çağırma.

**Sahne yığını.** Menüler oyunun *üstüne biner* (`blocks_update=True`,
`blocks_draw=False`). Asla ikinci bir `while` döngüsü açma — eski kodun en
büyük hatası buydu.

**Bölümler veri.** Yeni bölüm = `tools/make_levels.py` içine yeni ASCII +
sözlük girdisi. Kodda bölüm numarasına bakan `if` yazma.

### His ayarları

Oynanışın "hissi" [lore/entities/player.py](lore/entities/player.py) başındaki
sabitlerde. Tek tek değiştir, her değişiklikten sonra oyna:
`RUN_SPEED`, `JUMP_SPEED`, `COYOTE_TIME`, `APEX_GRAVITY`, `DASH_*`, `COMBO`.

### Zıplama zarfı — bölüm tasarımının sınırı

Ölçülmüş değerler (`python tools/measure_jump.py`): **60 px (3.75 tile) yükseklik,
92 px (5.75 tile) menzil.** Tasarım sınırları marjla bunun altında:

| Sabit | Değer | Anlamı |
|-------|-------|--------|
| `Level.MAX_JUMP_TILES` | 4 | Azami uçurum genişliği (kenarlar arası 5 tile yol) |
| `Level.MAX_JUMP_HEIGHT_TILES` | 3 | Basılabilir satırlar arası azami dikey adım |

**En sık yapılan hata:** Rey platformun *üstünde* durur, yani işgal ettiği satır
platform satırının bir üstüdür. 3 tile'lık bir adım için platform tepesi
2 satır yukarıda olmalı — 3 değil. Zemin tepesi 16 ise platform tepeleri
13, 10, 7 olur.

`Level.validate()` doğuş noktasından BFS yaparak erişilemeyen platform ve
prop'ları bildirir; `make_levels.py` bunu yazmadan önce çalıştırır. `JUMP_SPEED`
veya `RUN_SPEED` değişirse **önce `measure_jump.py` çalıştır**, sonra bu iki
sabiti güncelle, sonra `make_levels.py` ile bölümleri yeniden doğrula.

### Sprite hizalama

Sprite hücresi karakterden büyüktür (silahın savrulmasına yer bırakır), bu
yüzden ayakların altında boş piksel kalır. `Entity.sprite_foot_y`
(`CharSpec.foot_y`) hücre içindeki taban çizgisini tutar ve çizim bunu gövdenin
altına hizalar. Ayarlanmazsa karakter havada durur.

### Düşman AI sözleşmesi

`patrol → alert → chase → windup → attack → recover`. **Windup fazı zorunlu:**
saldırıdan önce görünür bir hazırlık ve renk uyarısı olmalı. Uyarısız saldıran
düşman "haksız" hissettirir.

Arkadan fark etme mesafesi (`sight_behind = 11`) yumruk menzilinden küçük
tutulmalı; aksi halde Act I'in tek saldırı yolu olan sırttan vuruş çalışmaz.
Koşarak yaklaşan oyuncu `sight_behind_running = 52` ile duyulur.

## Eski kod

`legacy/` altındaki dosyalar ilk sürümdür; referans olarak duruyor, çalışmıyor
ve içe aktarılmıyor. Yeni koda örnek alma.

## Yol haritası

[docs/ROADMAP.md](docs/ROADMAP.md) — 5 Act, 28 bölüm, faz faz plan.
