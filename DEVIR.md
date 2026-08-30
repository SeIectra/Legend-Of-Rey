# DEVİR — Legend of Rey (LORE)

**Bu proje hakkında tek devir belgesi budur.** Başka bir AI oturumuna
devredildiğinde okunması gereken tek dosya.

Okuma sırası: **1) `CLAUDE.md`** (bağlayıcı kurallar — anayasa) → **2) bu
dosya** (nerede kaldık) → 3) gerekirse `docs/` altındaki ilgili tasarım
belgesi.

Son güncelleme: **30.08.2026** (Bölüm 7 + sinematik sahneleme katmanı, oyun kolu ayarı, test paketi 97 sn) · Ardeko Studios · Arda Güner

> `GOREVLER.md` **silindi** (23.08.2026, Arda'nın isteği: "bir devir.md
> olsun diğerlerini sil kafa karıştırmasın"). İçindeki canlı bilgi bu
> dosyaya taşındı; eski hâli git geçmişinde duruyor.

---

## 1. OYUN NE

Pygame ile yapılan, yandan görünümlü aksiyon-RPG. Kafasının içindeki
sesler yüzünden lanetli sayılan **Rey**, kaçırılan kardeşi **Cemo**'yu
kurtarmak için zindana iner — ve o sesler ona yardım ederken, aslında onu
çağırıyordur.

**18 bölüm · ~4 saat · 2 oynanabilir karakter (Rey, Ardo) · PC (klavye +
gamepad) · mobil DEĞİL.**

Tasarım paketi `docs/` altında ve **bağlayıcı**: `gdd.md` (ana belge),
`dovus-sistemi.md` (kare değerleri), `yapi.md` (18 bölümün akışı),
`bolum-02.md` / `bolum-03.md` (oda oda tasarım), `menu-ui.md`,
`asset-plani.md`, `derinlestirme.md`, `ekonomi-uretim.md`,
`asset-listesi.md`, `asset-boru-hatti.md`.

---

## 2. NEREDE DURUYORUZ

**~37.000 satır Python. 26 test paketi de yeşil — ve artık 97 saniyede.**

Oynanabilir akış:
`intro → menü → karakter seçimi → dikey yolculuk → **Bölüm 1 (Köy)** →
**Bölüm 2 (İlk İniş)** → **Bölüm 3 (Meşale Mahzeni)** → **Bölüm 4 (Kayıt
Odası)** → **Bölüm 5 (Sular)** → **Bölüm 6 (ARDO)** → **Bölüm 7 (Dar
Geçit)** → bölüm sonu ekranı → ana menü`

Bölüm 7'nin sonu ana menüye dönüyor çünkü **Bölüm 8 henüz yok** — bilinçli
bir uç. **Katman 1 (Çürüyenler, B1–B6) tamamlandı; Katman 2 (Lanetli
Muhafızlar, B7–B13) başladı.**

### Açılış artık 0,4 saniye (30.08.2026)

Arda oyunun geç açıldığını söyledi. Ölçüldü: `pygame.joystick.init()` bu
makinede **40,30 saniye** sürüyor ve sıfır kol buluyor (NGENUITY/HyperX
kaynaklı bir sürücü sorunu, kodla ilgisi yok). Yedi SDL ipucu denendi,
etkisiz; ayrı iş parçacığına almak imkânsız (ölçüldü: ana iş parçacığı 40
saniyede **tek döngü turu** attı, GIL bırakılmıyor).

Çözüm tasarımsal ve Arda **B seçeneğini** seçti: kol desteği bir **ayar**,
varsayılanı kapalı. `Game.__init__` artık `pygame.init()` çağırmıyor
(`display.init()` + `font.init()`). Kolu olan oyuncu ayarı bir kez açıyor.
`tests/test_settings.py` varsayılanın kapalı kalmasını koruyor.

Aynı düzeltme test paketini de kurtardı: 21 paket `pygame.init()` çağırıp
o 40 saniyeyi ayrı ayrı ödüyordu. **14+ dakika → 97 saniye.** Bu arada
`test_combat` sessizce kırık çıktı (ortasında `pygame.quit()` vardı) —
kırıklığı 14 dakikanın arkasında görünmüyordu.

### Görev listesi (eski `GOREVLER.md`'den)

| # | Görev | Durum |
|---|---|---|
| 0 | Temel kurulum (palet, font, döngü, boru hattı) | ✅ |
| 1 | Dövüş çekirdeği (zincir, hitstop, kaçınma, kill cancel) | ✅ |
| 2 | Düşman AI (3 tip, saldırı hakkı, ritim imzaları) | ✅ |
| 3 | Yankı sistemi (3 kademe, yalan, pusula, kırılabilir duvar) | ✅ |
| 4 | Bölüm 2 — dikey dilim (8 oda, gizli oda, mini-boss) | ✅ |
| 5 | **Ara değerlendirme** | ⬜ **Arda'nın işi, Claude'a verilmez** |
| 6 | Menü ve UI | ✅ (sıra dışı yapıldı, Arda istedi) |
| 7 | Menü sahnesi cilası (mor alev, intro, dikey yolculuk) | ✅ |
| 8 | Bölüm 3 — Meşale Mahzeni | ✅ |
| 9 | Sanat geçişi | 🟡 sprite + tileset + post-fx var; 9-slice yok |
| 10 | Ses | 🟡 öncelik 1 seti sentezle var; müzik ve öncelik 2-3 yok |
| 11 | Değerlendirme (karar, kod değil) | ⬜ **Arda'nın işi** |
| 12 | Bölüm 4 — Kayıt Odası + **yetenek ağacı** | ✅ (29.08.2026) |
| 13 | Bölüm 5 — Sular + **su seviyesi mekaniği** | ✅ (29.08.2026) |
| 14 | **Kalkanlı** — Katman 2'nin ilk AI'ı | ✅ (29.08.2026) |
| 15 | **Bölüm 2 silah seçimi** (Hançer/Balta) | ✅ (29.08.2026) |
| 16 | **Kontrol noktası** — ölünce odanın başından devam | ✅ (29.08.2026) |
| 17 | **İz Sürme** — Ardo'nun karşı mekaniği | ✅ (29.08.2026) |
| 18 | **Portre sistemi + sprite oranları** | ✅ (29.08.2026) |
| 19 | **Bölüm 6 — ARDO** (yoldaş, plakalar, BOSS 1) | ✅ (29.08.2026) |
| 20 | **Oyun kolu ayarı** — açılış 40,7 sn → 0,4 sn | ✅ (30.08.2026) |
| 21 | **Sinematik sahneleme katmanı** (`staging.py`) | ✅ (30.08.2026) |
| 22 | **Bölüm 7 — Dar Geçit** (girth, çark, **el**) | ✅ (30.08.2026) |

**Bölüm 4 "Kayıt Odası"** (`docs/yapi.md` B4): yetenek ağacı sistemi
(`src/systems/skilltree.py` — 3 dal × 4 düğüm) + ağaç ekranı
(`src/ui/skill_tree.py`) + üç oda + günlük parçaları. Ağacın beş
toplayıcısı (`damage_scale`, `defence_scale`, `echo_sight_scale`,
`max_health_bonus`, `chain_window_bonus` …) gerçekten **bağlı** — bir
ara sürümde hesaplanıp hiçbir yerde okunmuyordu. Savunma çarpanı Yankı
cezasından **sonra** uygulanıyor: taş dalının işi tam olarak o cezayı
yumuşatmak.

**Bölüm 5 "Sular"** (`docs/yapi.md` B5): su tek bir **yatay düzlem**
(`src/world/water.py`), tile başına su yok — vana bir sayıyı değiştiriyor.
Kaldırma kuvveti `Body.gravity_scale` üzerinden, yani sudan çıkan gövde
**kendiliğinden** eski davranışına dönüyor. Batma bir **oran** (0..1),
eşik değil; eşik olsaydı su yüzeyinde gövde her karede girip çıkıp
titrerdi. Bulmaca dört adım, atlanamaz: alt geçidi şamandıralı bir savak
kapatıyor, yani ikinci vanaya çıkmak **zorunlu** (Bölüm 2/3'te boss
atlanabiliyordu — o ders `keydoor.py`'ye yazılmıştı, burada kilit
tasarıma gömülü).

### Grafik + anlatım geçişi — **YEDİ FAZ DA TAMAM (29.08.2026)**

Arda'nın 23.08.2026 isteği: *"grafikleri elinden geldiğince biraz daha
güzelleştir ve hikaye sunumları ile ara sinematikleri geliştir."*
Yedi faza bölündü:

| Faz | İş | Durum |
|---|---|---|
| **A** | Anlatım altyapısı (`story.py` panel sistemi, bölüm kartı, sinematikte diyalog) | ✅ |
| **B** | Bölüm 1 prologu — kolyenin verilişi | ✅ |
| **C** | Atmosfer + ışık (post-fx vinyet/tint, toz/zerre katmanı) | ✅ |
| **D** | Çevre ve dekor (köy, köylüler, gökyüzü katmanları) | ✅ |
| **E** | Karakter sprite'ları (silah izi, ikincil hareket, geçiş kareleri) | ✅ |
| **F** | HUD ve arayüz | ✅ bölmeli can çubuğu + hayalet, jeton solması, Yankı göstergeleri mor |
| **G** | Bölüm 2/3 anlatımı | ✅ B2 iniş sahnesi (`story.py`) · B3'e dört anlatım anı · Yankı/Ardo ayrımı üç bölümde de |

**Işık sistemi hakkında bir düzeltme (24.08.2026):** Bu belge bir ara
"ışık sistemi yalnızca Bölüm 3'e bağlı, B1/B2'ye de bağlanmalı" diyordu —
**yanlıştı.** `lighting.render` bir *tam karanlık maskesi*; Bölüm 3'ün
mekaniği ("Meşale Mahzeni") tam olarak o. Bölüm 1/2'ye takmak onları
oynanamaz yapardı. İkisinin de zaten meşale/yarık parıltısı (`radial_glow`)
var ve doğru görsel o. Işık huzmesi denendi, üç tur sonra kaldırıldı —
gerekçe `src/art/ambience.py` başında yazılı.

---

## 3. ARDA'NIN KARARLARI — PAKETE ÜSTÜN

Bunlar `CLAUDE.md` ve `docs/`'taki kuralları **bilinçli olarak** geçersiz
kılar. Kendiliğinden geri alma.

1. **Tam yetki (22.08.2026, tekrarlandı 23.08.2026).** Onay beklemeden
   ilerle, görevden göreve kendiliğinden geç. `CLAUDE.md` §13'ün "dur,
   sıradaki göreve kendiliğinden geçme" kuralını geçersiz kılar. Yine de:
   her iş sonunda **test kanıtı göster** ve **bu dosyayı güncelle**.

2. **400 satır sınırı kaldırıldı (23.08.2026).** `CLAUDE.md` §11 "400
   satırı geçen dosya bölünür" diyordu; Arda izin verdi. Bölmek yine de
   iyi bir refleks — `chapter01.py` üçe bölününce gerçekten okunaklı oldu
   — ama artık **zorunlu değil**.

3. **Palet 32 → 37 renk (23.08.2026).** Beş yeşil eklendi. Gerekçe ve
   ölçüm §5'te. `CLAUDE.md` §6'nın "32 renk sabit" ifadesi bu kadarıyla
   güncellendi; **palet dışı renk hâlâ yasak**, yeni renk için yine sor.

4. **numpy runtime bağımlılığı onaylandı.** Üçüncü bir kütüphane hâlâ
   izne tabi.

5. **Oyun artık diyalogsuz değil (22.08.2026).** `docs/gdd.md` §2'yi
   geçersiz kılar. **Sinematiklerde de konuşma var** (23.08.2026 kararı).
   Yankı'nın **kutusu yok** — kafadaki ses çerçeveli kutuya konmaz.

6. **Sprite'lar baştan açık.** Paket "Görev 1-4 boyunca kutularla oyna"
   diyordu. Yerine `F4` üç kip arasında geziyor: sprite → siluet → kutu.

7. **Karakter kanonu:**

   | Karakter | Cinsiyet | Görünüm |
   |---|---|---|
   | **Rey** | kadın (she) | Esmer, uzun düz koyu kahve saç, mavi savaş elbisesi, kırmızı pelerin, sağ köprücük altında geyik dövmesi |
   | **Ardo** | erkek (he) | İri savaşçı, geniş omuz, **koyu kısa saç**, gri kürk omuzluk, koyu zırh, büyük kılıç. Kukulete YOK. |
   | **Cemo** | erkek — Rey'in küçük kardeşi | Esmer, kıvırcık saç, çocuk oranları |

   **Bölüm 1 prologu iki karakter de oynuyor** (23.08.2026 kararı).
   Replikler bu yüzden **nötr** yazıldı (ne "abla" ne "kardeş" geçiyor) —
   Cemo'nun Rey'in kardeşi olduğu kanon bozulmadan Ardo oynanışında da
   doğru okunuyor. **Ardo'nun motivasyonu yazıldı (24.08.2026):** Yankı
   Rey'in laneti olduğu için Ardo onu **duymuyor** — yalnız iniyor, ve bu
   bir eksiklik değil karakter farkı. Kendi üç repliği var: kolyeye
   teşekkür, yarığı tanıması ("Bu yarığı daha önce gördüm"), ve inme
   gerekçesi ("Aşağıda ne olduğunu biliyorum. Onu orada bırakamam").

8. **Düşman katman sırası DEĞİŞMEDİ** (23.08.2026'da tartışıldı, Arda
   mevcut sırayı onayladı). Ama şu eklendi: **bir sonraki katmanın en
   kolay üyesi bir bölüm erken tanıtılacak** — B5'te tek bir Kalkanlı,
   B12 civarında ilk Sessiz. Çeşitlilik erken gelsin, öğretme sırası
   bozulmasın.

9. **Goblin ayrı düşman olarak eklenmiyor** — Katman 2'nin **Kalkanlı**'sı
   goblin'in ruhuyla yapıldı (yeşil ten, sivri kulak, bıçak+kalkan).

10. **Mor Alev meşale kısıtından muaf** (Görev 8). `docs/bolum-03.md`
    açıkça söylemiyor; sönmez ve doğaüstü olduğu için tek-elli dövüş
    kısıtı (2'li zincir) uygulanmıyor.

11. **`src/scenes/` eklendi** — `CLAUDE.md` §5'teki yapıda yok, mimari
    serbest olduğu için eklendi.

12. **Aseprite kurulmadı**, şimdilik gerek yok. Hazırlığı var
    (`tools/aseprite.py`, `tools/palette_to_gpl.py`).

---

## 4. ÇALIŞTIRMA VE DOĞRULAMA

```bash
.venv/Scripts/python.exe main.py           # intro → ana menü
.venv/Scripts/python.exe main.py dovus     # dövüş test odası
.venv/Scripts/python.exe main.py bolum3    # doğrudan Bölüm 3
```

Python 3.14, pygame-ce 2.5.8, numpy. Sanal ortam `.venv/`.

### Her değişiklikten sonra — istisnasız

```bash
for f in tests/test_*.py; do .venv/Scripts/python.exe "$f" || echo "KIRIK: $f"; done
.venv/Scripts/python.exe tools/reachability.py      # HER ODA GEÇİLEBİLİR Mİ
```

13 test paketi: `test_foundation` (palet, font, tr_upper, atmosfer katmanı),
`test_pipeline` (quantize→outline→shade), `test_combat` (**bağlayıcı kare
değerleri**), `test_menu`, `test_lang`, `test_window`, `test_enemy`,
`test_echo`, `test_level`, `test_dialogue`, `test_chapter01/02/03`.

`test_combat.py` `docs/dovus-sistemi.md`'deki her sayının kodda tuttuğunu
kanıtlar. Bir değer sessizce değişirse orası kırılır — **bu kasıtlı.**

### Görsel doğrulama — "çalışıyor" demeden önce BAK

```bash
.venv/Scripts/python.exe tools/shot.py --scene src.scenes.chapter01:Chapter01Scene --frames 60 --out build/testshots/x.png
.venv/Scripts/python.exe tools/roster.py                  # 10 düşmanın kadro sayfası (normal + siluet)
.venv/Scripts/python.exe tools/sprite_sheet.py --siluet   # siluet testi
.venv/Scripts/python.exe tools/measure_jump.py            # zıplama zarfı
```

Çıktılar `build/testshots/` altına düşer. `CLAUDE.md` §13 bakmayı **şart
koşuyor**.

**`tools/reachability.py` yeni bölüm yazarken şart.** Zıplama zarfını
ölçüp haritada BFS yürüyor; şimdiye kadar 5 gerçek hata yakaladı. Yeni
bölüm eklerken `_known_rooms()` içine eklemeyi unutma — eklenmeyen oda
doğrulanmaz ve sessizce bozuk kalır.

---

## 5. MİMARİ — HIZLI HARİTA

```
src/
├── config.py          TÜM sayısal değerler, KARE cinsinden. Sihirli sayı yok.
├── core/
│   ├── game.py        Sabit 60 kare döngü, 480×270, tam sayı ölçekleme, post-fx
│   ├── scene.py       Sahne yığını (tek döngü kuralı — ikinci while ASLA)
│   ├── input.py       Aksiyon eşlemesi + 8 karelik tampon
│   ├── camera.py      Takip, ölü bölge, ileri bakış
│   └── juice.py       ★ on_hit() — hitstop+sarsıntı+parçacık TEK çağrıdan
├── art/
│   ├── palette.py     37 renk, tools/palette.json'dan. Palet dışı YASAK.
│   ├── forge.py       İndeks tabanlı çizim (renk değil, zincir+basamak)
│   ├── spritegen.py   draw_humanoid — tek iskelet, çok karakter
│   ├── animation.py   Poz üreticileri + KARAKTER KÜTÜPHANESİ (10 düşman + 4 kişi)
│   ├── animator.py    Oynatıcı + sprite önbelleği
│   ├── particles.py   Olay parçacıkları (vuruş/ölüm), üst sınır 200
│   ├── ambience.py    ★ SÜREKLİ atmosfer (toz/gece zerresi/kor) — parallax'lı
│   ├── postfx.py      ★ Vinyet + bölüm renk derecelendirmesi
│   ├── lighting.py    Karartma + ışık delikleri (ŞU AN SADECE B3)
│   ├── tileset.py     Prosedürel tuğla/kiriş/diken
│   └── wind.py        Dikey dilim kaydırma (pelerin, saç, bayrak)
├── combat/
│   ├── combo.py       3'lü zincir (chain_table silaha göre), kaçınma, sayaç
│   ├── weapons.py     yumruk/kılıç/hançer/balta kaydı
│   ├── attack_token.py ★ aynı anda en fazla 2 saldırgan
│   └── hitbox.py      Kare bazlı — kimse doğrudan hasar vermez
├── entities/          actor · player · player_render · character_stats · dummy
│   ├── enemy.py       Durum makinesi, tell, poise
│   ├── enemy_navigation.py  Dikey erişim + kenar kaçışı
│   ├── enemies/       shambler · climber · bloated · bloated_one ·
│   │                  shadow_shambler · extinguished_one
│   ├── villager.py    ★ Bölüm 1 köylüsü — gezinir, tehlikede eve kaçar
│   ├── candle_keeper.py  Bölüm 3 tüccarı
│   └── boss.py        Faz geçişleri + can barı
├── systems/           save (yedekli) · settings · echo · compass · light ·
│                      economy · abilities · charms
├── ui/                text (tr_upper!) · widgets · menu · character_select ·
│                      settings_scene · pause · hud · font_data · cursor ·
│                      dialogue · chapter_card ★ · balloon · echo_view
│   ├── i18n.py        t() — TR/EN, çizim anında çözülür
│   └── lang/          tr.json (kanonik) · en.json
├── world/             tilemap · decals · level · pickups · torch
│   ├── cave_backdrop.py      Yeraltı arka planı (B2, B3)
│   ├── village_backdrop.py ★ Köy + gökyüzü katmanları (B1)
│   └── rooms/         chapter01 · chapter02 · chapter03 — ASCII oda verisi
└── scenes/            combat_room · foundation_check · intro · menu_reveal ·
                       vertical_journey · cinematic · chapter01/02/03 ·
                       chapter01_render ★ · chapter03_cinematics
    ├── play.py        ★ PlayScene — bütün game feel kancaları BURADA
    └── story.py       ★ Panelli anlatım katmanı (letterbox, kamera, replik)
```

### Değiştirmeden önce bilinmesi gerekenler

- **Zaman birimi karedir.** `dt` yok. Hız piksel/kare, ivme piksel/kare².
- **Renkle değil, gölge zinciriyle çizilir.** `forge.Canvas` her piksel
  için (zincir, basamak) tutar; `shade()` ve `outline()` bunun üstünde.
- **Hasar tek yerden geçer.** `hitboxes.spawn(Hitbox(...))` →
  `HitboxManager` çözer → `scene.on_hit()` game feel'i verir.
  `take_damage` doğrudan çağrılmaz.
- **`smoothscale` yasak** (ışık/bulanıklık katmanı hariç).
- **Türkçe:** yorumlar ve commit mesajları Türkçe, tanımlayıcılar
  İngilizce. Büyük harf için **her yerde** `text.tr_upper()`.

---

## 6. PAHALIYA ÖĞRENİLENLER — TEKRARLAMA

Hepsi gerçek hataydı, çoğu testle yakalandı.

1. **`convert()`/`convert_alpha()` `display.set_mode()`'dan önce
   çağrılamaz.** `Game.__init__` içinde pencere önce açılır.
2. **Kill cancel AKTİF karelerde tetiklenmeli.** Sadece `RECOVERY`'ye
   bakmak mekanizmayı pratikte hiç çalıştırmaz.
3. **Sprite ayak hizalaması.** Hücrenin altı ≠ karakterin ayağı.
   `sprite_foot_y` kullanılmazsa karakter havada durur.
4. **Gölge zincirleri monoton parlaklaşmalı.** Ters dönen zincir
   ışıklandırmayı tersine çevirir.
5. **Zıplama zarfı ölçülür, tahmin edilmez.** `PLAYER_JUMP_SPEED`
   değişirse **önce** `tools/measure_jump.py`.
6. **Boşluk genişliği ≠ atlanacak mesafe.** N tile boşluk = N+1 tile yol.
7. **Kayıt sırası:** önce yeni kaydı yaz, **sonra** eskisini yedekle.
8. **`BLEND_RGB_ADD` alfayı yok sayar.** Şiddeti `set_alpha` ile değil,
   `BLEND_RGB_MULT` ile ayarla.
9. **Arayüz metni asla koda gömülmez.** `src/ui/lang/*.json`, çizim
   anında `t()`. **Anahtarlar düz yazılır** — f-string ile kurulanı
   `test_lang.py` göremiyor ve "ölü anahtar" sayıyor (bu tuzağa 4 kez
   düşüldü).
10. **`pygame.SCALED` KULLANMA.** Ölçek tam sayı olmak zorunda değil ve
    `get_size()` fiziksel değil mantıksal boyut döner.
11. **Bölüm haritası yazınca `tools/reachability.py` çalıştır.**
12. **Arka planda boş karanlık bırakma — "gökyüzü" gibi okunur.** Mağara
    arka planında da köy arka planında da aynı tuzağa düşüldü. Boşluğu
    **mesafeye** çevirmek gerekiyor (uzak siluet katmanı).
13. **Çizilen her ışık kaynağı bir şeye bağlı olmalı.** Sabit satıra
    konan meşalelerin yarısı havada asılı kaldı.
14. **`body_colour` RENK adı tutar, gölge zinciri adı DEĞİL.** Aynı sınıf
    hata `CharSpec` alanlarında da yaşandı (`"bile"` renk, `"rot"`
    zincir). Yeni spec yazarken `palette.json`'un `shade_chains`
    anahtarlarına bak.
15. **Test kendi koşulunu kurduğundan emin olmalı.** Düşmanlar odaya
    yayılmıştı, altısının ancak ikisi oyuncuyu görüyordu — asıl soru hiç
    sorulmuyordu ama test geçiyordu. Aynı sınıf: kolye testi
    `make_scene()` kullanıyordu, o yardımcı prologu **atlıyor**.
16. **Yazılıp hiç çalıştırılmayan kod hatasız görünür, değildir.**
    `tileset.py` iki görev boyunca "yazıldı ama bağlanmadı" diye durdu;
    bağlanır bağlanmaz üç yerde var olmayan zincir adına başvurduğu
    ortaya çıktı. `Boss.draw_health_bar` da vardı, hiçbir sahne
    çağırmıyordu.
17. **`elif` iki koşulu "ya biri ya öbürü" sanmak.** İkisi aynı anda
    doğru olabiliyorsa iç içe `if` kur ki hangi dalın önceliği olduğu
    açıkça yazılsın (`Climber._think_hanging`).
18. **Paylaşılan sınıfa "bir yer için" davranış eklerken varsayılan eski
    davranışı korumalı.** `Dialogue`'un otomatik ilerlemesi ilk hâlde
    koşulsuzdu ve Bölüm 2/3'ün repliklerini de sessizce etkiliyordu →
    `auto_advance=False` varsayılan oldu.
19. **Teleport ile test etmek gerçek senaryoyu atlayabilir.** Mini-boss
    kapısının oyuncuyu duvara gömme hatası, `teleport()` tabanlı testlerin
    atladığı bir kare penceresindeydi. **Yürünen senaryoyu test et.**
20. **Gövdesi katı tile ile ÇAKIŞAN aktör tamamen donar.** Hiçbir yöne
    kımıldayamaz ve `grounded=True` bildirir. Çarpışma çözücünün
    "çakışmadan dışarı it" kurtarma yolu yok. Aynı sınıf hata **üç kez**
    çıktı: mini-boss kapısının oyuncuyu gömmesi, Tırmanan'ın tavana
    gömülü doğması, ve bir testin oyuncuyu platformun içine koyması.
    Bir şeyi elle konumlandırırken (spawn, teleport, tilemap değişikliği)
    gövdenin **tamamının** boş tile'da olduğunu doğrula.

21. **Ekranda verilen her söz tutulmalı.** Ölüm ekranı "R ile sıfırla"
    yazıyordu ama `K_r`'yi yalnızca dövüş odası dinliyordu. Yıllarca
    zararsız göründü; arena çıkışı anahtarla açılır olunca gerçek bir
    yumuşak kilide dönüştü. Bir metin bir tuştan söz ediyorsa o tuşun
    çalıştığı **test edilmeli**.

22. **`pygame.quit()` bu makinede ÇOK pahalı.** Ölçüldü (cProfile):
    `Game.shutdown()` sonrası bir sonraki `pygame.init()` **40 saniye**
    sürüyor. Kodla ilgisi yok, SDL yeniden başlatma maliyeti. Testler
    bunu 25 kez ödüyordu (suite 20+ dk). **Testte `Game`'i yeniden
    yaratma** — sahne durumu zaten `set_root` ile sıfırlanıyor. Tek
    `Game`, sonda tek `shutdown()`.

23. **İki yerde aynı matematik = sessiz kayma.** Silah izi kılıcın
    ucundan çıkmalı; formülleri `draw_humanoid`'den kopyalasaydık biri
    değiştiğinde iz kılıçtan kayardı ve bunu ancak ekran görüntüsüne
    bakınca fark ederdik. `spritegen.weapon_tip()` **aynı** iskelet
    zincirini paylaşıyor, `WEAPON_LENGTH` de silah boylarının tek
    kaynağı.

24. **Heredoc (`<<'EOF'`) Türkçe metin ve ters bölü ile güvenilmez.**
    Uzun metni Write aracıyla yaz, kısa yamaları Python betiğiyle uygula.
    `\n` kaçışları iki kez yorumlanıp gerçek satır sonuna dönüşebiliyor.

---

## 7. 23.08.2026 GRAFİK KIYASLAMASI — ÖLÇÜLDÜ

Arda: *"prototype'taki oyun daha iyi duruyor ama nedenini anlamadım."*
`_prototype/` ile ölçülebilir karşılaştırma yapıldı. **"Prototipin 70
rengi vardı" hipotezi YANLIŞ çıktı:** tek sprite başına renk sayısı
goblin 15, Sürüklenen 11, Rey 16 — hiçbiri 32'ye yaklaşmıyor.

Gerçek beş sebep ve çözümleri:

1. **Prototipin HER düşmanında siluetten taşan bir parça vardı** (bıçak,
   yay, boynuz, kafatası); bizim üçünde de `weapon="none"` idi.
   → `shield/claws/spikes/crest/tail/hunch` alanları + spear/bow/axe.
2. **Kafa gövdeden açık değildi** — Sürüklenen'in kafası görünmüyordu.
3. **Gövde parlaklık aralığı:** Tırmanan **0.153** (hair/cloth/cloth_dark
   üçü de `"shadow"` idi), prototip iskelet **0.722**.
   → Zincirler ayrıldı.
4. **Boyut hiyerarşisi yoktu** — üç düşman da 40×36. Prototipte 32'den
   72'ye yayılıyordu.
5. **Post-fx katmanı hiç yoktu.** ← *"oyunun tamamı daha iyi duruyordu"nun
   asıl cevabı.* → `src/art/postfx.py` yazıldı.

**Palet:** 32 rengin ton dağılımında **hiç yeşil yoktu** (10 mavi, 9
turuncu, 7 kırmızı, 3 camgöbeği, 3 mor, **0 yeşil**). Bu yüzden `rot`
(çürüme) zinciri Yankı'nın camgöbeğine bağlanmıştı — düşmanların turkuaz
görünmesinin sebebi. Beş yeşil eklendi (32→37), `rot` ve `moss`
zincirleri kuruldu, renk körlüğü varyantları yeniden üretildi.

---

## 8. DÜŞMAN KADROSU — 10 TİP

`docs/gdd.md` §7. **Sanat hepsinin hazır** (`tools/roster.py` ile
görülebilir); Katman 2 ve 3 **hiçbir bölüme yerleştirilmedi** —
`CLAUDE.md` §3: ileri bölüm içeriği sırası gelmeden yazılmaz.

| Katman | Bölümler | Öğrettiği | Düşmanlar | Durum |
|---|---|---|---|---|
| **1 — Çürüyenler** | B1–B6 | combo **kurmayı** | Sürüklenen, Tırmanan, Şişmek | ✅ **tamamlandı** — B6 finali dahil |
| **2 — Lanetli Muhafızlar** | B7–B13 | combo'yu **kırmayı** | Kalkanlı, Mızraklı, Okçu, Komutan | ✅ dördü de tamam, **dördü de yerleşti** (B13) |
| **3 — Yankı'nın Çocukları** | B14–B18 | yardımcının ihaneti | Sessiz, Yankılayan, Bölünen | ✅ **üçü de tamam** (30.08.2026) |

**On düşman AI'ının onu da yazıldı.** Katman 2'nin dördü aynı cümleyi
dört ayrı dilbilgisiyle soruyor — Kalkanlı *yönle*, Mızraklı *mesafeyle*,
Okçu *zamanla*, Komutan *sayıyla*. Katman 3'ün üçü ise oyuncuya değil
**yardımcı sistemin kendisine** saldırıyor: Sessiz onu eksiltiyor
(Yankı göstermiyor), Yankılayan kirletiyor (sahte işaret), Bölünen
oyuncunun kendi becerisini aleyhine çeviriyor (combo çoğaltıyor).

Hiçbiri henüz bir bölüme **yerleştirilmedi** (Okçu/Komutan B13'e,
Katman 3 B14+'a ait) — `CLAUDE.md` §3: sırası gelmemiş bölüm içeriği
yazılmaz. Davranış hazır, yerleşim sırası gelince.

### Bölüm 6 "ARDO" — Katman 1'in finali (29.08.2026)

`docs/yapi.md` B6 + `docs/gdd.md` 10. **Üç yeni sistem** bir arada:

1. **Yoldaş** (`src/entities/companion.py`). Kim olduğu **kanondan**
   türüyor — `docs/gdd.md` §3: *"Seçmediğin, ara sahnelerde havalı girişi
   yapan taraf olur."* `Enemy` değil `Actor` alt sınıfı (saldırı hakkı /
   kuşatma yörüngesi düşmana ait). **Ölmez, diz çöker** — ölmesi dövüşü
   koruma görevine çevirir *ve* plaka bulmacasını çözülemez yapar.
   **Yardım eder, oynamaz:** hasar 7 (oyuncunun ilk vuruşu 10), vuruş
   aralığı 62 kare, tasma 120 px.
2. **Ağırlık plakaları** (`src/world/plate.py`). Kapı **bütün** plakalar
   aynı anda basılıyken açılıyor; tek kişi ikisine birden basamaz. Kapı
   bir bilmece değil bir **anlaşma** — B6'nın anlatısını anlatı
   söylemeden kapı yapıyor. Yarım saniyelik tolerans: sıfır olsaydı aynı
   *karede* basmak gerekirdi, bir yapay zekayla imkânsıza yakın.
3. **BOSS 1: Çürümüş Olan** (`src/entities/bosses/rotted_one.py`). Üç
   fazın her biri bir Katman 1 düşmanını geri getiriyor (Sürüklenen →
   Tırmanan → Şişmek): boss yeni bir şey öğretmiyor, **tier'ın sınavını**
   yapıyor. Üç hamle üç farklı çözüm istiyor.
   **Faz 2'nin mührü team-up'ın girdiği yer:** boss mühürlü, hiçbir vuruş
   işlemiyor; mühür yalnızca arena plakaları basılıyken kırılıyor ve 150
   kare (beş tam zincir) pencere açılıyor. Hasar *azalmıyor*, **geçmiyor**
   — azalma sayısal olurdu ve oyuncu farkı görmezdi.

**Öğret, sonra sına:** Oda 3 plakayı dövüşsüz öğretiyor, Oda 4 dövüşün
ortasına koyuyor (`docs/gdd.md` §9).

**Konuşma yok.** Yoldaş bölüm boyunca tek kelime etmiyor; Yankı da yoldaş
hakkında konuşmuyor — o an B8'e ait. Soru işareti **iki karakterin
arasında** duruyor (ilk sürümde oyuncunun tepesindeydi ve "oyuncu şaşırdı"
gibi okunuyordu; tarif edilen şey bir **bakışma**).

---

### Karakter sanatı — portre sistemi (29.08.2026)

Arda: *"Karakterler basit pixel bloklarından oluşmuş gibi değil,
profesyonel bir retro RPG'deki özenle çizilmiş karakterler gibi
görünmeli. Gözleri iki piksel nokta olarak bırakma… çocuk gibi veya chibi
görünmesin."* İstek 64×96 sprite'tı; **ölçüm başka bir cevap verdi.**

| Ölçülen | Değer |
|---|---|
| Rey'in eski çizilen boyu | 14×29 px, kafa 8 px = **3.5 kafa** (chibi) |
| Oyunun en dar yürünebilir geçidi | **2 tile = 32 px** (B1 (20,11), B2 (26,13)) |
| Oyuncu gövdesi | 10×22 |

64 piksellik karakter 32 piksellik koridordan geçemez — beş bölümün oda
geometrisi + zıplama zarfı + reachability doğrulaması çöper. 8 piksellik
kafada göz kapağı/iris/highlight/burun kümesi/dudak da **fiziksel olarak
sığmıyor**. Bu yüzden istek **iki katmana** bölündü:

1. **Portre** (`src/art/portrait.py`, 64×96, kafa 40 px) — yüzün gerçekten
   yaşadığı yer. Göz beş katman (kapak, sklera, iris, pupil, sol-üstte
   tek highlight); kaş eğimi **tek sayının işaretiyle** iki ifade
   (Rey +1 açık, Ardo −1 çatık); burun kısa sırt + uç kümesi + kanat
   gölgesi; ağız dört satır. Oranlar klasik çizim şemasından, elle
   ayarlanmadı. `shade()` bilerek çağrılmıyor — o geçiş gözün
   highlight'ını "kenar" sanıp eziyor.
   Bağlandığı yerler: **diyalog kutusu** ve **karakter seçimi**.
   Yankı'nın portresi **yok** — kafadaki sesin yüzü olmaz.
2. **Oyun içi sprite** — 32 px bütçesi içinde: 3.5 → **4.7 kafa boyu**,
   beli olan altı köşe gövde, **boyun**, daire olmayan kafa, saç çizgisi
   üst üçte bire indi, gövde içi hacim sütunları.

**İki yeni bağlayıcı kural** (`CLAUDE.md` §6'ya yazıldı, ikisi de
`tests/test_sprites.py` ile korunuyor ve birbirine **karşı** çalışıyor):
sprite ≤ 32 px, kafa/boy ≥ 4.4. Elden geçirme sırasında boy bir ara 35'e
çıktı ve **ancak ölçüldüğü için** fark edildi.

Siluet testi de gerçek hale geldi: kutu karşılaştırması kötü bir vekildi
(Sürüklenen ile Tırmanan'ın kutusu aynı, siluetleri bambaşka). Artık
maske IoU'su; ölçülen en dar çift **rey/ardo %25.3**.

---

### Bölüm 7 "Dar Geçit" — Katman 2'nin ilk bölümü (30.08.2026)

`docs/yapi.md` B7. Beş oda: Kapı Önü → Çarkhane → **El** → Geçit → Çıkış.

**Kanon `girth`'e bağlı, oynanan karaktere değil.** Çatlaktan her zaman
Rey geçiyor (girth 10 ≤ açıklık 12), Ardo hiçbir zaman (15 > 12). Bu iki
farklı oynanış üretiyor ve ikincisi tematik olarak daha da doğru:

* **Rey oynanırken** — sen geçiyorsun, çarkı sen çeviriyorsun.
* **Ardo oynanırken** — sen geçemiyorsun. Yoldaşı (Rey) çatlağa
  **gönderiyorsun** (`Companion.hold`, Bölüm 6'nın plaka emriyle aynı
  tuş), çarkı o çeviriyor, kapıyı sana o açıyor. Bölüm 6'da kurtaran
  taraftın; burada bekleyen taraf.

Uçurum ne atlanarak ne tırmanarak geçiliyor — **sayılar hesaplandı, tahmin
edilmedi**: karşı duvar 4 tile (`MAX_JUMP_HEIGHT_TILES` = 3), yatay
açıklık 6 tile (`MAX_JUMP_GAP_TILES` = 4). Çukura düşmek kilitlemiyor:
sol tarafta basamaklar var. `tests/test_chapter07.py` üçünü de ölçüyor.

`tools/reachability.py`'ye eklendi. Kapı **açık**, çukur **dolu** hâlde
doğrulanıyor (Bölüm 6'nın köşe duvarıyla aynı gerekçe). Çukuru `ignore`'a
atmak yerine doldurmak bilinçli: ignore edilseydi ötesindeki iki oda da
doğrulama dışında kalırdı.

*Not:* kapı ilk sürümde tek sütun açılıyordu — duvar üç tile kalın olduğu
için açılınca duvarın içinde bir çukur oluşuyordu ve kimse geçemiyordu.

### Sinematik sahneleme katmanı (30.08.2026)

Arda: *"Daha fazla sinematik ara sahne koyalım. Animasyonlu ve efektli
sahneler."*

Ortaya çıkan asıl eksik şuydu: **bugüne kadarki ara sahnelerde tek bir
karakter çizilmemişti.** Bölüm 3'ün "Mor" sahnesi büyüyen bir daire,
"İniş" küçülen bir daire. Oysa 20 karakterin 12 animasyon durumu zaten
üretilmiş ve `Animator.render()` yön/flaş/deformasyon/siluet/tint/alfa'yı
zaten destekliyor.

`src/scenes/staging.py` o boşluğu dolduruyor. `StoryScene`'in `Panel`
diline bir `Cue` katmanı ekliyor — kim, ne zaman, ne yapıyor:

    Panel(90, "el", cues=(
        Cue("above", state="idle", face=-1),
        Cue("below", move_to=(222.0, GROUND_Y), move_frames=40, state="jump"),
    ))

Getirdikleri: gerçek sprite'lı aktörler, yumuşatılmış hareket, parçacık,
eklemeli ışık, kenar ışığı (`rim_light`), vinyet, ekran flaşı, zemin
gölgesi, **tam sayı sinematik büyütmesi** (yakın planda 2×; 32 piksellik
figür 480×270'lik bir karede duygusal an için küçük kalıyordu).

Bölüm 7 bunu dört sahnede kullanıyor: **Mühür** (bölüm açılışı, Katman
2'nin ilk görüntüsü), **Sığmıyor** (yoldaş çatlağa giremiyor — tek kelime
yok), **Yalnız** (vinyet kapanıyor), **El** ★.

**"El" sahnesinde tek replik yok** — `docs/yapi.md`'nin açık talimatı
(*"Balon yok — sadece bir saniye fazla tutulan el"*). Anlam sürede:
eller birleştikten sonra sahne 60 kare daha bekliyor (`HOLD_TOO_LONG`).
Test bu iki şartı da koruyor. Müzik `Raze` (Arda: *"çok nadir duygusal
kısımlar için"*) — bütün oyunda bir kez çalan parça.

*Üç kez düşülen tuzak, üçüncüsü burada:* vinyet önce `set_alpha()` ile
yazıldı. `BLEND_RGB_SUB`/`ADD` **alfayı yok sayar** (`glow.py`'nin kendi
başlığında yazıyor) — karartma her zaman tam güçteydi ve iki sahne
simsiyah çıktı. Şiddet artık renk ölçekleyerek veriliyor.

### Rey'in "sakalı" (30.08.2026)

Arda: *"Rey yaptığın gölgelendirmeden dolayı sakallı gibi duruyor."*
Haklıydı ve **iki ayrı yerde** aynı hata vardı:

* `spritegen.py` — çene gölgesi çenenin tam **ortasına**, ağzın altına
  konuyordu; bu ölçekte bir sakal lekesinin durduğu tek yer orası.
  Gölge silinmedi, çenenin karanlık yanına taşındı ve bir adım açıldı.
* `portrait.py` — çene altı ve sağ çene kaması `step=0` ile
  boyanıyordu. `skin_tan`'ın 0. basamağı `earth_dark`, yani **saç rengi
  ailesi**. Göz onu gölge diye değil sakal diye okuyor. En koyu basamak
  bir piksellik kontura çekildi.

Ardo'nun sert çenesi etkilenmedi: onunki `stubble=1` + `face_shadow=1`
ile ayrıca çiziliyor.

### Kalkanlı — Katman 2'nin ilk AI'ı (29.08.2026)

`src/entities/enemies/shieldbearer.py`. B5'te **tek örnekle** tanıtıldı
(§3 madde 8). Sonraki üç Katman 2 düşmanı bunun desenini izlemeli:

- **Ders metinle değil oyuncunun kendi sayacıyla veriliyor:** önden vuran
  oyuncunun **zinciri kırılıyor**, combo sayacı sıfırlanıyor. Blok hasar
  vermiyor — ceza can değil **ritim**. Can cezası olsaydı oyuncu deneme
  yapmaktan korkar ve dersi hiç bulamazdı.
- **İki geçerli cevap, bilerek iki tane:** (1) arkaya geç — kaçınma
  düşmanın içinden geçiyor, arkadan gelen vuruş tam hasar + **kesin
  sendeleme**; (2) saldırısını yemle, toparlanırken vur — kalkan sadece
  beklerken yukarıda. Tek cevap bırakmak daha "saf" olurdu ama daha kötü.
- **Dönme gecikmesi tek ayar düğmesi.** `Enemy._face_player()` anında
  dönüyor; Kalkanlı onu **ezmek zorunda**, yoksa arkaya geçmek imkânsız
  olur. 34 kare sonra dönüyor, ama önce 10 kare parlıyor ve duruyor —
  sessizce dönmek "arkasındayım" sözleşmesini bozardı.
- **Kalkan gövdeye bağlı, ele değil** (`spritegen.py`). Ele bağlıyken
  bıçakla birlikte savruluyordu, yani "ön hat duvar" okuması tam da
  saldırı anında kayboluyordu.
- **Zeminle çözülen su sorunu:** Oda 3'ün tabanı bir tile yükseltildi.
  Su tek düzlem ve düşmanlara da uygulanıyor; kod istisnası yazmak
  "suda düşman yok" kararını gizlerdi.

Artı **4 büyük boss** (B6, B13, B14, B18) ve her bölümde bir mini-boss
("mevcut düşmanın büyütülmüş hâli, bir ek hamle" — bilinçli olarak ucuz).
Yapılan mini-boss'lar: Şişmiş Olan (B2), Sönmüş Olan (B3).
**Yapılan büyük boss: Çürümüş Olan (B6, BOSS 1)** — üç fazı Katman 1'in
üç düşmanından alıyor, Faz 2'nin mührü ağırlık plakalarıyla kırılıyor.
Kalan üçü (B13, B14, B18) sırası gelmedi.

---

### Bölüm 13 "Cemo" — BOSS 2 ve zaman kapıları (30.08.2026)

B12 atlandı, B13 önce yazıldı: yeni mekanik + BOSS 2 orada, B12 ise
nefes bölümü (`docs/yapi.md`: *"sıfır dövüş kodu ister"*). Zincirleme
B12 gelince kurulur — `main.py`'de not düşülü.

**Zaman kapıları** (`src/systems/timegate.py`). On iki bölümdür doğru
olan cümleyi bozuyor: *odayı temizle, sonra geç.* Kol çevriliyor, sürgü
iniyor, yoldaki her düşman **zaman** demek. Odalara konan iki düşman
bu yüzden Okçu ve Komutan — ikisi de "önce beni hallet" diye bağıran
düşmanlar, ve ikisinin de doğru cevabı burada hayır.

Sayaç **HUD'da değil, kapının kendisi**: sürgü indikçe boşluk azalıyor,
oyuncunun boyundan kısalınca geçiş kapanıyor. Kapı açıkken bile
görünüyor (tavan yuvasına çekilmiş halde) — ilk sürümde görünmüyordu
ve oyuncu nereye koşacağını bilmiyordu; ekran görüntüsü gösterdi.

**Süreler tahmin değil ölçüm.** Ölçüt: en yavaş karakterin (Ardo,
1.8 px/kare) koldan kapıya düz koşu süresi, ve pencerenin ondan en az
1.35 kat uzun olması. İlk yerleşimde Oda 6 **0.71x** çıktı — yani
kusursuz oynayan biri bile geçemezdi. `tests/test_chapter13.py` her
çalışmada yeniden ölçüyor. Zorluk sayacın küçüklüğünden değil
**mesafeden** geliyor: tile başına düşen süre 21.8 → 18.7 → 14.0 →
12.5.

**BOSS 2 "Zindancı"** (`src/entities/bosses/gaoler.py`, 64×80 —
oyunun en büyük sprite'ı). Çürümüş Olan Katman 1'in sınavıydı; bu
Katman 2'nin, çünkü Katman 2 burada bitiyor:

    Faz 0  GARDİYAN  Kalkanlı   YÖN      önden geçmez
    Faz 1  ZİNCİR    Mızraklı   MESAFE   menzilinin dışından
                     Okçu       ZAMAN    uçan anahtarlar
    Faz 2  ZİNDAN    Komutan    SAYI     çağırıyor + fener kırılıyor

**Feneri** tek imzası: arena karanlık, o taşıyor. Yani alışıldık boss
ritmi tersine dönüyor — uzaklaşırsan görmüyorsun. Her fazda bir kademe
soluyor, faz 2'de kırılıyor. Ardından mangallar (B3'ün ışık sistemi,
`docs/bolum-03.md`: *"ışıkla arena kontrolü → B13"*) tek kaynak.

Karanlık **tell'i gizlemiyor** (`CLAUDE.md` §7 bağlayıcı): gözleri bir
ışık kaynağı ve tell'de büyüyor. Karanlık konumu gizler, niyeti değil.
Oyuncunun kendi ışığı **kolye** — kendini ve kılıç menzilini görüyor,
boss'u değil. İlk sürümde bu yoktu ve arena oynanamayacak kadar
karanlıktı; yine ekran görüntüsü gösterdi.

Rey'in Yankısı bu fazda doğal avantaj ama **kodda hiçbir istisna yok**:
`echo_view.draw_reveal` zaten düşmanları çiziyor. Asimetri yazılmadı,
var olan sistemlerden düştü.

**Dört ara sahne** (`chapter13_cinematics.py`), kafes sahnesi
`skippable=False` — B3'ün "Mor" sahnesinden sonra bunu yapan ikinci
sahne. Gerekçe aynı: geçen şey bilgi değil **kayıp**.

### Beş gizli hata — hepsi tek bir eksik test yüzünden (30.08.2026)

Zindancı'nın feneri `self.frames` okuyordu ve `Enemy`de öyle bir alan
yoktu. Onu kovalarken ortaya beş ayrı hata çıktı ve **beşi de canlı
içerikte duruyordu**:

1. **`Enemy.draw` yoktu.** Mızraklı/Okçu/Komutan doğrudan `Enemy`den
   türüyor ve `Actor.draw` soyut. **Bölüm 11 gerçekten çöküyordu** —
   salondaki Mızraklı kameraya girdiği an `NotImplementedError`.
2. **`draw_extra`'yı hiçbir şey çağırmıyordu.** Komutan'ın sancağı,
   Okçu'nun yay gerilimi, Sessiz'in gözleri, Yankılayan'ın sahte
   işareti — hepsi ölü kod. Üçü tell'in kendisiydi, biri bir düşmanın
   **bütün mekaniği**.
3. **Altı düşman `silhouette_scale()` metodunu bir float ile
   gölgeliyordu.** Yani tell'deki siluet şişmesi — `CLAUDE.md` §10'un
   renk körlüğü garantisi — ölüydü, ve çizim `TypeError` veriyordu.
4. **Yankılayan'ın nabzı negatife düşüyordu** (`0.45 + 0.55*sin`),
   `surface.fill` "invalid color" atıyordu.
5. **`palette.color("brass")`** — zincir/renk tuzağına dördüncü kez
   düşüldü.

Ortak sebep: **testler hiç çizim çağırmıyordu.** Davranış yeşildi,
görüntü çökük. Üç kalıcı önlem yazıldı:

  * `tests/test_enemies.py` her düşmanın `draw`/`draw_extra`sını
    90 kare + tell boyunca çalıştırıyor, ve `silhouette_scale`ın
    metod olduğunu **ve tell'de gerçekten şiştiğini** ölçüyor.
  * `tests/test_pipeline.py` bütün `palette.color("...")` çağrılarını
    tarıyor — zincir adı geçerse kırılıyor.
  * `tests/test_audio.py`'nin deseni genişletildi: `tell_sound = "x"`
    gibi boşluklu atamalar görünmüyordu, uydurma `shield_clang` tam
    o delikten geçmişti.

Ders şu: bir düşmanın sözleşmesi yalnızca ne yaptığı değil, **ekranda
görünebildiği** de.

## 9. AÇIK KALANLAR

Sırası gelmediği için değil, **gözden kaçmasın** diye:

1. **Işık sistemi yalnızca Bölüm 3'e bağlı.** B1'in yarığı ve B2'nin
   meşaleleri gerçek ışık vermiyor. (Faz C'nin yarım kalan parçası.)
2. ~~Katman 2'de sadece Kalkanlı'nın AI'ı var~~ — **kapandı
   (30.08.2026).** On AI'ın onu da yazıldı; `tests/test_enemies.py`
   her birinin `docs/gdd.md` §7'deki cümlesini gerçekten yaptığını
   ölçüyor. Kalan iş yerleştirme, davranış değil.
3. ~~Ardo'nun oynanışı Rey'in aynısı~~ — **kapandı (29.08.2026).**
   `src/systems/tracking.py` + `src/ui/tracking_view.py`. Aynı tuş, zıt
   bilgi: Rey geleceği/gizliyi **duyar**, Ardo geçmişi **görür**. Eğri
   birebir aynı (girdi ortak), menzil bilerek farklı (Yankı 260/96/0 —
   bir lanet, ölümle zayıflar; İz Sürme sabit 190 — zayıflamaz ama
   berrak Yankı kadar da görmez). Bedel: Yankı ekranı **karartır**,
   İz Sürme **ağartır** ve yaşayan düşmanlar %62 solar.
   **Eşitlik yapısal:** Yankı ne açıklıyorsa İz Sürme de açıklıyor
   (kırılabilir duvarlar), gerekçe farklı — Rey duvarın arkasını duyar,
   Ardo duvardan birinin geçtiğini görür. Bölüm verisine tek satır
   eklenmedi; `CLAUDE.md` §3 sırası gelmemiş içeriği yasakladığı için
   eşitliğin yapısal olması şarttı.
4. **Ardo'nun Bölüm 1'deki motivasyonu yazılmadı** (bkz. §3 madde 7).

4b. **Tuş yeniden atama arayüzü yok.** `CLAUDE.md` §10 zorunlu tutuyor;
   `settings.py` `bindings` değerini tutuyor ama onu değiştiren bir ekran
   yok. Arda 30.08.2026'da kol ayarını seçerken *"Tuşları falan da
   ayarlara getiririz"* dedi — sırası geldi.

4c. **Bölüm 1-6'nın ara sahneleri hâlâ eski dilde.** `staging.py` artık
   var ama yalnızca Bölüm 7 kullanıyor; Bölüm 2/3'ün sinematikleri hâlâ
   renkli daireler. Geriye dönük çevirmek ucuz (`Panel` zaten ortak) ve
   oyunun ilk yarısını belirgin biçimde iyileştirir.
5. **Boss kapısı + anahtar (24.08.2026)** — `src/world/keydoor.py`.
   Bölüm 2 ve 3'ün arena çıkışı kilitli, boss ölünce anahtar düşüyor.
   Aynı yapı sonraki boss odalarında da kullanılmalı; Bölüm 2/3'e
   bakarak bağlanır (`_drop_key` / `_update_key`).
   *Bölüm 5'te gerekmedi* — orada kilit **tasarıma gömülü** (savak su
   seviyesini izliyor). Kilit bir mekanizma değil, bir sonuç olduğunda
   daha iyi okunuyor; boss odaları dışında bu yol tercih edilmeli.

6. ~~Bölüm 2'nin ödülü eksik~~ — **kapandı (29.08.2026).**
   `src/ui/weapon_choice.py`. Boss ölünce 100 kare sonra açılıyor
   (öldürme anında açmak zaferi keser), iptal yok (bu bir menü değil
   **ödül**), sayılar `config.py`'nin zincir tablolarından **okunuyor**
   (elle yazılsa ilk denge geçişinde yalan olurdu). Ölüm ödül vermiyor:
   `_open_arena(defeated=False)`. Hançer/Balta'nın kendi sprite'ları var.
   Seçim `PlayScene._equip_saved_weapon()` ile sonraki bölümlere
   taşınıyor — **yalnızca Hançer/Balta**, yoksa kaydın varsayılan
   "sword" değeri Bölüm 1'in "kılıcı buluyor" anını bozardı.
7. **`tools/reachability.py` Bölüm 5'i yalnızca KURU doğruluyor.** BFS
   suyu bilmiyor; su yüzeyini "platform" sayan ikinci bir geçiş denendi
   ve **yanlış** çıktı (yüzmek "yüzeyde yürümek" değil, su hacminde
   yükselmek). Üst kat `validate(..., ignore=)` ile "bilerek erişilemez"
   kümesine alındı — yoksa araç sürekli kırmızı yanar ve zamanla göz ardı
   edilirdi. Su yolu bunun yerine `tests/test_chapter05.py` içinde
   **gerçek fizikle** oynatılıyor. *Aynı desen ileride bir mekanik
   BFS'e sığmadığında tekrar kullanılmalı: aracı zorlama, testi yaz.*
8. ~~Checkpoint yok~~ — **kapandı (29.08.2026).** `PlayScene.restart()`
   artık **odanın** başından devam ettiriyor. Kısmi geri alma değil:
   sahne yine **tamamen** baştan kuruluyor (yoksa kapı/anahtar/arena
   mührü/su seviyesi gibi değişmezlerden biri mutlaka bayat kalır),
   sonra oyuncu ölduğü odanın başına ışınlanıyor ve o odanın düşmanları
   yeniden doğuyor. Alt sınıflar bunun için **hiçbir şey yapmıyor** —
   hepsi zaten `self.room` tutuyor, `PlayScene` o değişimi izliyor.
   Yalnızca **yerdeyken** kaydediliyor (havada kaydedilse boşluğa düşen
   oyuncu sonsuz ölüm döngüsüne girerdi).
9. **Müzik yok.** Ses efektleri var (sentezlenmiş). **Döngülü/sürekli
   sesler bilerek kaldırıldı** — Arda: *"cızırtı gibi, rahatsız edici"*.
   Altyapı (`play_loop`/`stop_loop`) duruyor, kullanılmıyor. Gerçek kayıt
   gelirse tekrar açılabilir.
10. **`game.music_hush` dolduruluyor ama kimse okumuyor.** Görsel yarısı
   çalışıyor, müziği kısacak taraf müzik gelince yazılacak.
11. **EKSTRALAR ve EKİPMAN menüde kapalı.**
12. **Bölüm 3'ün "5 yuva" ödülü basitleştirildi** — belge "ısıyla açılan
    gizli kapı" tarif ediyor, kodda kutlama efekti/toast var.
13. **Gerçek 9-slice tileset yok** (köşe/kenar ayrı parça). Şu anki
    dikdörtgen blok tasarımı için yeterli görünüyor.
14. **`docs/asset-plani.md` güncel değil** — "Türkçe karakter eksik" ve
    "prototipteki sprite kalitesi" maddeleri artık geçersiz.
15. **`_prototype/` referans, ASLA import etme.** İçinde işe yarar
    fikirler var (parallax, post-fx, ışıklandırma, tile üreteci).

---

## 10. GİT

Uzak depo: `https://github.com/Ardeko/Legend-Of-Rey.git` · dal: `main`

> **`git push` bu ortamda ÇALIŞMIYOR** — kimlik doğrulama yok
> (`fatal: could not read Username for 'https://github.com'`). Commit'ler
> yerelde birikiyor. Başka bir makineden ya da kimlik bilgisi girilmiş
> bir oturumdan push gerekiyor. **Devralan oturum bunu önce kontrol
> etsin:** `git log origin/main..main --oneline`

Eski motor `v2.1` etiketinde. Commit mesajları **niçin** öyle yapıldığını
anlatıyor — bir davranışı değiştirmeden önce ilgili commit'e bakmakta
fayda var.

Commit'lenmiş hiçbir şey kaybolmaz: `git log --oneline --all`,
`git reflog`.

Commit mesajları Türkçe ve şununla bitiyor:
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`

---

## 11. ÇALIŞMA DÜZENİ

1. `CLAUDE.md`'yi oku, sonra bu dosyayı, sonra `docs/`'tan ilgili belgeyi
2. Büyük işte **önce plan sun** (Arda tam yetki verdi ama plan yine iyi
   fikir — bir özellik 20 karar noktası içerir)
3. Kodu yaz
4. **Çalıştır ve kanıt göster** — test çıktısı, komut, **ekran görüntüsü**.
   "Çalışıyor" deme, göster.
5. Ne yaptığını özetle, açık kalanları söyle
6. **Bu dosyayı güncelle** (Arda'nın açık isteği, 23.08.2026)
7. Sıradaki işe geç — Arda "sormadan devam et" dedi

**Sandbox'ta çalışmayan bir adım varsa görevi "tamamlandı" ilan etme.**

### Efor kademesi (Arda'nın sorusu üzerine, 23.08.2026)

- **Max** — varsayılan. Tek şeritli görsel/tasarım döngüsü (sprite yaz →
  çiz → bak → düzelt) burada en verimli.
- **Ultracode** (xhigh + çok-ajanlı paralel dağıtım) — yalnızca
  **parçalara ayrılıp doğrulanması gereken geniş iş** için: Katman 2
  düşman AI'ları (4 bağımsız dosya), Bölüm 6 (team-up + ilk büyük boss),
  18 bölüm bittikten sonra bütünsel denge geçişi.
  *Bölüm 4 ve 5 bu listedeydi, ikisi de Ultracode'da yapıldı ve bitti.*
- Bu projede fan-out'un gerçek riski var: her alt-ajan **soğuk başlıyor**
  ve bu repo bağlayıcı geleneklerle dolu (37 renk paleti, zincir-adı
  tuzağı, Türkçe yorumlar, kare tabanlı zamanlama, sıra kuralı). Bağlam
  kaybı bu projedeki hataların ana kaynağı oldu.
