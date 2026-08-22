# DEVİR — Legend of Rey

Bu belge, projeyi devralan Claude Code oturumu içindir.
**Önce `CLAUDE.md`'yi oku** (bağlayıcı anayasa), sonra burayı.

Son güncelleme: 23.08.2026 (üçüncü canlı oynanış geri bildirim turu sonrası) · Ardeko Studios

---

## 1. NEREDE DURUYORUZ

18 bölümlük yandan görünümlü aksiyon-RPG. Tasarım paketi `docs/` altında,
görev sırası `GOREVLER.md`'de.

| Görev | Durum | Not |
|---|---|---|
| 0 — Temel kurulum | ✅ | Palet, font, döngü, boru hattı |
| 1 — Dövüş çekirdeği | ✅ | Zincir, hitstop, kaçınma, kill cancel |
| 2 — Düşman AI | ✅ | 3 tip, saldırı hakkı, ritim imzaları |
| 3 — Yankı sistemi | ✅ | 3 kademe, yalan, kolye pusulası, kırılabilir duvar |
| 4 — Bölüm 2 | ✅ | Dikey dilim — 8 oda, gizli odacık, mini-boss |
| 5 — Ara değerlendirme | ⬜ | **Arda'nın işi**, Claude'a verilmez |
| 6 — Menü ve UI | ✅ | Sıra dışı yapıldı (Arda istedi) |
| 7 — Menü sahnesi cilası | ✅ | Mor alev, Ardeko intro, dikey yolculuk |
| 8 — Bölüm 3 | ✅ | Meşale Mahzeni: ışık sistemi, 7 oda + gizli Mum Bekçisi cebi, mini-boss |
| 9 — Sanat geçişi | 🟡 | Sprite + mağara arka planı + **tileset artık bağlı**; ses hâlâ eksik |
| 10 — Ses + son cila | 🟡 | Öncelik 1 seti sentezle bağlandı; müzik/öncelik 2-3 yok |

Toplam ~13.900 satır. **On üç test paketi de yeşil** (`test_chapter01.py` +
`test_chapter03.py` eklendi).

**Oynanabilir akış:**
intro → menü → karakter seçimi → dikey yolculuk → **Bölüm 1 (Köy)** →
**Bölüm 2 (İlk İniş)** → bölüm sonu ekranı → **Bölüm 3 (Meşale Mahzeni)** →
bölüm sonu ekranı → ana menü

Bölüm 2'nin sonu artık Bölüm 3'e zincirleniyor (`chapter02.py::_end_chapter`
`on_continue` ile `DescentCinematic`'i açıyor). Bölüm 3'ün sonu şimdilik ana
menüye dönüyor çünkü Bölüm 4 henüz yok - bilinçli bir uç.

**Arda'nın seçtiği sıra:** Görev 7 ✅ → Bölüm 1 + prolog ✅ → Görev 3 ✅ → Görev 4 ✅

**Kanon kararları:**
- Goblin ayrı düşman olarak eklenmiyor; Katman 2'nin **Kalkanlı**'sı
  goblin'in ruhuyla yapılacak (Görev 4+).
- **Oyun artık diyalogsuz değil** (22.08.2026). `docs/gdd.md` §2'yi geçersiz
  kılar. Konuşma bir kanal *ekliyor*; jest ve ikon balonu duruyor.
  Yankı'nın **kutusu yok** — kafadaki ses cerçeveli kutuya konmaz.

---

## 2. ARDA'NIN VERDİĞİ KARARLAR — pakete ÜSTÜN

Bunlar `CLAUDE.md` ve `GOREVLER.md`'deki kuralları bilinçli olarak geçersiz
kılar. Kendiliğinden geri alma; Arda'ya sormadan değiştirme.

1. **numpy runtime bağımlılığı onaylandı.** `CLAUDE.md` §4'te not düşüldü.
   Üçüncü bir kütüphane hâlâ izne tabi.

2. **Sprite'lar baştan açık.** Paket "Görev 1-4 boyunca kutularla oyna"
   diyordu; Arda "sprite'lar kalsın" dedi. Yerine `F4` üç kip arasında
   geziyor: `sprite → silhouette → box`. Kutu kipi kuralın ruhunu koruyor.

3. **Menü (Görev 6) sıradan önce yapıldı.** Oyunun gösterilebilir bir yüzü
   olsun diye.

4. **Hikâye paketten:** kaçırılan **Cemo**, **Ardo** ikinci oynanabilir
   karakter, para **Altın**, 18 bölüm. Rey'in göğsündeki **geyik dövmesi**
   kişisel simgesi olarak korunuyor (Arda'nın isteği, paketle çelişmiyor).

5. **Karakter kanonu — Arda belirledi.** Çeviride zamir gerektiği için
   cinsiyetler bağlayıcı:

   | Karakter | Cinsiyet | Görünüm |
   |---|---|---|
   | **Rey** | kadın (she) | Esmer, uzun gür düz koyu kahve saç, koyu kahve badem gözler, pürüzsüz cilt, rahat feminen giyim, sağ köprücük kemiği altında **geyik dövmesi** |
   | **Ardo** | erkek (he) | Geniş omuz, gümüş/gri kısa saç, ağır duruş, pelerin (kukulete kaldırıldı - §2 madde 13) |
   | **Cemo** | erkek — Rey'in **küçük kardeşi** | Esmer, **kıvırcık** saç, tatlı/yakışıklı bir çocuk |

   Cemo'nun sprite'ı **henüz üretilmedi** — Bölüm 1 ve 13 içeriği, sırası
   gelmedi (`CLAUDE.md` §3). Tarif burada duruyor ki sırası gelince
   tahmine kalmasın. Kıvırcık saç Rey'in düz saçından ayrışıyor, siluet
   testinde işe yarayacak.

6. **`src/scenes/` eklendi** — `CLAUDE.md` §5'teki yapıda yok, mimari serbest
   olduğu için eklendi.

7. **Aseprite:** kurulmadı, şimdilik gerek yok. Hazırlığı yapıldı
   (`tools/aseprite.py` tespit + geri düşüş, `tools/palette_to_gpl.py`,
   `.gitattributes`). Arda lisansı onayladı; elle rötuş gerektiğinde kurulur.

8. **Tam yetki (22.08.2026, PC'den uzun süre uzak kalacağı için).** Arda
   Claude'a onay beklemeden ilerleme ve **görevden göreve kendiliğinden
   geçme** izni verdi - CLAUDE.md §13'ün "dur, sıradaki göreve kendiliğinden
   geçme" kuralını bilinçli olarak geçersiz kılıyor. Bu izin devam ediyor
   sayılmalı; geri alındığına dair açık bir mesaj gelmedikçe sıradaki görevi
   sormadan başlat. Yine de: her görev sonunda test kanıtı göster ve bu
   belgeyi güncelle - "durmadan devam etmek" "sessizce ilerlemek" demek
   değil.

9. **Mor Alev'in meşale kısıtlamasından muaf tutulması (Görev 8).**
   `docs/bolum-03.md` bunu açıkça söylemiyor; Mor Alev sönmez ve doğaüstü
   olduğu için (sıradan elde tutulan bir meşale değil) tek-elli dövüş
   kısıtını (2'li zincir, bitirici yok) uygulamıyorum
   (`Chapter03Scene._update_combo_restriction`). Yanlışsa tek satırlık bir
   değişiklik.

10. **Silah sistemi genelleştirildi (22.08.2026).** Arda: "sadece yumruk,
    sonra kılıç iyi. ama sonrasında bölüm 2 mini boss sonrası hançer/balta
    olayı devam etsin. hatta gelecekte ok/arbalet de koyabiliriz... önce
    altyapıyı kur." Eski davranış (kılıç yokken saldırı **tamamen kilitli**)
    değişti: Rey artık yumrukla başlıyor, saldırı bastan açık; kılıç
    Bölüm 1'de bulununca `equip_weapon()` ile üstüne biniyor. Yapılan:
    - `src/config.py`: `FIST_CHAIN`/`DAGGER_CHAIN`/`AXE_CHAIN` — **açıkça
      placeholder**, sayıları henüz Arda belirlemedi. Bağlayıcı `CHAIN`
      (kılıç) tablosuna dokunulmadı.
    - `src/combat/weapons.py` (yeni): `Weapon` kaydı + `starting_weapon()`
      (Rey→yumruk, Ardo→kılıç). Hançer/Balta **tanımlı ama hiçbir sahne
      henüz vermiyor** — ödül akışı ayrı bir görev (madde 9 altta).
    - `ChainState`'e `chain_table` alanı: artık hangi silahın zincirini
      okuyacağını `Player` söylüyor, modül sabiti `CHAIN`'e kilitli değil.
    - `Player.equip_weapon()` yeni, `_equip_sword()`'un yerini aldı;
      `grant(SWORD)` artık bunu çağırıyor.
    - `tests/test_combat.py` "yetenek kapisi" bölümü güncellendi: eski
      iddia ("kılıç yokken saldırılamaz") artık **yanlış** — yeni iddia
      yumrukla saldırının çalıştığını, kılıcın `chain_table`'ı bağlayıcı
      `CHAIN`'e değiştirdiğini doğruluyor.
    - Hançer/Balta'nın kendi sprite'ı yok, `sword`'la aynı `_armed`
      varyantını **bilerek** paylaşıyorlar (CLAUDE.md: sessiz placeholder
      yasak, bu yüzden `weapons.py` docstring'inde açıkça yazılı).

11. **Tileset nihayet bağlandı (22.08.2026, Görev 9).** `src/art/tileset.py`
    daha önce yazılmış ama hiç çalıştırılmamış "ölü kod"du - bağlanınca
    hemen üç `PaletteError` verdi: `_brick_wall`/`_spike` var olmayan
    `"stone"`/`"danger"` **zincirlerini** çağırıyordu (ikisi de sadece renk
    adı/ramp, `tools/palette.json`'un `shade_chains` bölümünde yok).
    Düzeltme: duvar → `"steel"` zinciri (ramps.stone ile birebir aynı 4
    ton, sadece adı zırhtan geliyor), diken → `"gore"` (danger_bright'a
    ulaşan tek zincir), platform (ahşap kiriş) → `"leather"` (earth_dark/
    earth içeren tek 4 basamaklı zincir). Palete **yeni renk eklenmedi** -
    sadece var olan zincirlerden doğru olanı seçildi. `world/tilemap.py`
    artık düz renk doldurmuyor, `TileSet.wall/platform/spike()`'tan blit
    ediyor; kırılabilir duvar hâlâ normal duvarla **aynı üretici**yle
    çiziliyor (aynı (tx,ty) → aynı varyant), ayırt edilemezlik korundu.

12. **Ses sistemi + canlı geri bildirim (22.08.2026, Görev 10).** Ses
    tasarımcısı/kayıt bu ortamda yok; `src/audio/` altında numpy ile
    sentezlendi (CLAUDE.md 6: "kod ile üret" ilkesinin sese uygulanışı).
    Arda oynarken hemen iki şey bildirdi, ikisi de **aynı oturumda**
    düzeltildi:
    - **"sesler çok rahatsız edici ve uyumsuz."** Üç neden bulundu: (a)
      `ui_tick`/`ui_deny`/`ui_slider` kare dalga (square wave) kullanıyordu
      - sert/8-bit bip, oyunun karanlık tonuyla çelişiyor - sinüse
        çevrildi; (b) adım sesi 11px'te bir tetikleniyordu (koşarken ~11
        ses/sn) - `STEP_DISTANCE_PX` 42'ye çıkarıldı (~2.5 adım/sn); (c)
        genel `normalize()` tepe genliği 0.92 - sentez için çok agresif,
        0.55'e düşürüldü. **Kesin çözüldüğü doğrulanmadı** - Arda'nın
        kendi kulağıyla onaylaması gerekiyor, dönünce sorulmalı.
    - **"ilk bölümde duvara sıkıştım yine boss'tan önce."** Araştırma:
      Bölüm 2'nin arena kapısı (daha önce düzeltilmişti) bot-yürüyüş
      testiyle doğru çalıştığı görüldü; asıl suçlu Bölüm 3'ün mini-boss
      arenasıydı ("Sönmüş Olan") - **aynı hatanın Bölüm 3'e hiç
      taşınmamış hâli**: oda sınırına girer girmez mühürleniyordu.
      `world/rooms/chapter03.py`'ye `ARENA_DOOR_COLUMN` eklendi,
      `_update_arena()` eşik+tampon geçilince mühürlüyor - Bölüm 2'nin
      kalıbıyla birebir. `tests/test_chapter03.py` regresyon kontrolü var.

13. **Ardo "insana benzemiyor" → kukulete tamamen kaldırıldı (22.08.2026).**
    İki turlu geri bildirim. İlk tur: `hood=True` karakterlerde yüzün çoğu
    "shadow" zinciriyle karartılıyordu ve gözler "hair_dark" ile
    çiziliyordu - ikisi de aynı derecede koyu, gözler gölgede tamamen
    kayboluyordu. Gölge yarıçapını küçültüp gözleri soluk "bone_pale"
    yaptım - **yetmedi**. İkinci tur, daha net: "kafasındaki o şey yüzünden
    yaratığa benziyor, havalı ve yakışıklı bir karakter çiz demiştim."
    Kukuletenin **şekli** kendisi (sivri, asimetrik) küçük tuvalde
    "insan" değil "yaratık" okunuyordu - yüz kısmen görünür olsa bile.
    Karar: kukulete tamamen kaldırıldı (`hood=False`), Rey'inki gibi
    tam açık yüz + gümüş/gri kısa saç (`hair="steel"` - Rey'in koyu uzun
    saçından hem renk hem siluet olarak ayrı). Geniş omuz/omuz zırhı/
    pelerin duruyor - siluet ayrımı hâlâ korunuyor (`tools/sprite_sheet.py
    --siluet` ile doğrulandı). Ardo'nun `cloth_dark`'ı da "shadow" (arka
    planla aynı ton) yerine "steel" oldu (eteği olmadığı için arka bacak
    doğrudan görünüyordu ve kayboluyordu).

    **Üçüncü tur (22-23.08.2026), referans karakter görselleri geldikten
    sonra:** Arda iki AI üretimi karakter referans sayfası + "havalı ve
    yakışıklı" tarifini gönderdi. Üç ayrı ince ayar:
    - `shoulder_chain: str = ""` alanı `CharSpec`'e eklendi (boşsa
      `armor`'a düşer) - Ardo'ya zırhla aynı tona karışmayan, ayrı
      açık/kürk tonlu (`"bone_pale"`) omuz yastığı verildi.
    - **Saç rengi `"steel"` → `"hair_dark"`** (Rey'le AYNI zincir).
      Referans görseldeki saç koyuydu; gri sadece Rey'den ayrışsın diye
      seçilmişti. Siluet testi yalnızca **şekle** bakıyor (tek renge
      düzleşir) - rengi koyulaştırmak Rey/Ardo ayrımını bozmuyor, ayrım
      zaten geniş omuz + kısa saç siluet şekli + kürk yaka + eteksizlikle
      taşınıyor. `tools/sprite_sheet.py --siluet` ile yeniden doğrulandı.
    - Referans görsellerdeki boyalı/yüksek-çözünürlüklü stil (ve "Muhafız"
      karakteri, Rey için "büyü" animasyonları) **birebir kopyalanmadı** -
      `CLAUDE.md`'nin bağlayıcı boru hattı el çizimi/dışarıdan görsel almayı
      yasaklıyor, yalnızca prosedürel + 32 renk palet + kod-üretimi sprite
      kabul ediyor. Arda'ya bu kısıt açıkça söylendi; tarif edilen
      özellikler (silah/kimlik okunabilirliği, "havalı" duruş) motor
      sınırları içinde karşılandı.

---

## 3. ÇALIŞTIRMA VE DOĞRULAMA

```bash
.venv\Scripts\python.exe main.py          # ana menü
.venv\Scripts\python.exe main.py dovus    # doğrudan dövüş odası
.venv\Scripts\python.exe main.py temel    # Faz 0 doğrulama ekranı
```

Python 3.13.15, pygame-ce 2.5.8, numpy. Sanal ortam `.venv/`.

### Testler — değişiklikten sonra hepsini çalıştır

```bash
for f in tests/test_*.py; do python "$f" || echo "KIRIK: $f"; done
```

Tek tek:

```bash
python tests/test_foundation.py   # palet 32 renk, Türkçe font, tr_upper
python tests/test_pipeline.py     # quantize → outline → shade → preview
python tests/test_combat.py       # dövüş kare değerleri (BAĞLAYICI)
python tests/test_menu.py         # menü UX + kayıt güvenliği
python tests/test_lang.py         # dil tabloları + kod/tablo örtüşmesi
python tests/test_window.py       # tam ekran / ölçekleme matematiği
python tests/test_enemy.py        # saldırı hakkı, tell, ritim, ekoloji
python tests/test_echo.py         # Yankı kademeleri, yalan, EKRAN PARLAKLIĞI
python tests/test_level.py        # bölüm haritaları zıplama zarfına uyuyor mu
python tests/test_dialogue.py     # Yankı'nın kutusu yok, kutu boyutu sabit
python tests/test_chapter02.py    # Bölüm 2 başsız oynanıyor — 40 kontrol
python -m pyflakes src tools tests main.py
```

`test_combat.py` `docs/dovus-sistemi.md`'deki her sayının kodda tuttuğunu
kanıtlar. Bir değer sessizce değişirse orası kırılır — **bu kasıtlı.**

### Görsel doğrulama

```bash
python tools/shot.py --scene src.ui.menu:MainMenuScene --out build/x.png
python tools/sprite_sheet.py --karakter rey --durum idle,run,attack1
python tools/sprite_sheet.py --siluet          # siluet testi
python tools/measure_jump.py                   # zıplama zarfı
python tools/reachability.py --ayrinti         # HER ODA GEÇİLEBİLİR Mİ
```

**`tools/reachability.py` yeni bölüm yazarken şart.** Zıplama zarfını
ölçüp haritada BFS yürüyor. Bölüm 1'de iki, Bölüm 2'de üç gerçek hata
yakaladı (mühürlü oda, havada doğum noktası, erişilemez platform).
Yeni bölüm eklerken `_known_rooms()` içine eklemeyi unutma — eklenmeyen
oda doğrulanmaz ve sessizce bozuk kalır.

Ekran görüntüleri `build/testshots/` altına düşer. **"Çalışıyor" deme,
görüntüyü aç ve bak** — `CLAUDE.md` §13 bunu şart koşuyor.

---

## 4. PAHALIYA ÖĞRENİLENLER

Bunların hepsi gerçek hataydı, testle yakalandı. Tekrarlama.

1. **`convert()` / `convert_alpha()` `display.set_mode()`'dan önce çağrılamaz.**
   `Game.__init__` içinde pencere önce açılır, canvas sonra oluşur.

2. **Kill cancel AKTİF karelerde tetiklenmeli.** Düşman hitbox açıkken ölür;
   yalnızca `RECOVERY`'ye bakmak mekanizmayı pratikte hiç çalıştırmaz.
   `ChainState.skip_recovery` bunun için var.

3. **Sprite ayak hizalaması.** Hücrenin altı ≠ karakterin ayağı.
   `sprite_foot_y` (= `CharSpec.foot_y`) kullanılmazsa karakter havada durur.
   Squash yüksekliği değiştirdiği için taban çizgisi de ölçeklenir.

4. **Gölge zincirleri monoton parlaklaşmalı.** Ters dönen bir zincir
   ışıklandırmayı tersine çevirir; `hair_dark` bir kez bu hataya düştü.

5. **Siluet testi işe yarıyor.** Rey ve Ardo ayırt edilemiyordu; Ardo'ya sivri
   kukulete ve geniş omuz verildi. Yeni karakterde mutlaka çalıştır.

6. **Zıplama zarfı ölçülür, tahmin edilmez.** `PLAYER_JUMP_SPEED` ya da
   `PLAYER_RUN_SPEED` değişirse **önce** `tools/measure_jump.py`, sonra
   `config.py`, sonra bölüm doğrulaması. Prototipte bu atlandığı için bir
   bölümün çıkış kapısına ulaşılamıyordu.

7. **Boşluk genişliği ≠ atlanacak mesafe.** N tile genişliğindeki boşluk,
   kenardaki basılabilir tile'lar arasında N+1 tile yol demek.

8. **Kayıt sırası önemli:** önce yeni kaydı diske yaz, **sonra** eskisini
   yedekle. Tersi, yazma çökerse iki bozuk dosya bırakır.

9. **Panel yükseklikleri içerikle hesaplanmalı.** İki menü panelinde son satır
   çerçeveyi kesiyordu.

10. **`BLEND_RGB_ADD` alfayı yok sayar.** Şiddeti `set_alpha` ile değil,
    renkleri `BLEND_RGB_MULT` ile kısarak ayarla.

11. **Arayüz metni asla koda gömülmez.** `src/ui/lang/*.json` içine dil
    anahtarı olarak yazılır, çizim anında `t()` ile çözülür. Modül
    seviyesinde sabit metin dil değişimini etkisiz bırakır.

12. **Dile bağlı olduğu fark edilmeyen şeyler:** yüzde işaretinin yeri
    (TR `%100`, EN `100%`), süre birimi (`dk`/`m`), ve büyük harf kuralı —
    `tr_upper("Continue")` noktalı İ ile `CONTİNUE` verir.

13. **Hitbox sahibini vurmaz.** Yakın dövüşte fark edilmiyordu (kutu önde
    açılıyor); radyal patlamada kutu patlayanın üzerinde duruyor, ilk hedef
    kendisi çıkıyor ve `pierce=False` ise orada tükeniyor — patlama kimseye
    ulaşmıyor.

14. **`body_colour` RENK adı tutar, gölge zinciri adı değil.** `"rot"` bir
    zincir; kutu kipi ilk açılışta `PaletteError` ile çöküyordu. Kutu kipi
    hata ayıklama yolu olduğu için normal oyunda aylarca görünmeyebilir.

15. **Kalıcı durum için `tint_strength < 1.0` kullan.** Tam güç sprite'ı tek
    renge düzleştirir — iki karelik vuruş flaşı için doğru, "az can" gibi
    ölene kadar süren bir durum için değil. Ayrıca çok silik bir tint hiçbir
    bilgi vermez: 0.30 denendi, sağlam düşmandan ayırt edilemiyordu.

16. **Test kendi koşulunu kurduğundan emin olmalı.** Düşmanlar odaya
    yayılmıştı, altısının ancak ikisi oyuncuyu görüyordu — "kalabalık
    okunabilir mi?" sorusu hiç sorulmuyordu ama test geçiyordu.

17. **`pygame.SCALED` KULLANMA.** O bayrak pygame'in kendi ölçeklemesini
    devreye sokar ve ölçek tam sayı olmak zorunda değildir: 1920×1080
    ekranda mantıksal 1440×810 yüzey 1.333× gerilir, piksel art bozulur.
    Ayrıca `screen.get_size()` fiziksel değil **mantıksal** boyutu döner,
    yani viewport hesabı gerçek ekranı hiç görmez. Ölçeği kendimiz
    hesaplıyoruz (`viewport_for()`), `tests/test_window.py` bekçilik ediyor.

18. **Bölüm haritası yazınca `tools/reachability.py`'ı çalıştır — istisnasız.**
    Bölüm 2'nin ilk hali üç ayrı biçimde bozuktu ve hiçbiri ASCII bloğa
    bakınca görünmüyordu: doğum işareti zeminin bir tile üstündeydi
    (`R` satır 12'de, zemin 14'te), Oda 1/4A/8 kendi yan duvarlarıyla
    tamamen mühürlüydü (odayı çerçevelemek istemiştim, geçişi kapatmışım),
    Oda 3 ve 7'nin platformları 4 ve 6 tile yukarıdaydı — zarf 3.
    Elle oynayarak bulmak yarım saat sürerdi; araç iki saniyede söyledi.

19. **Arka planda boş karanlık bırakma — "gökyüzü" gibi okunur.** Mağara
    arka planının ilk hali düz tepeli dikdörtgenlerdi ve ekranda net bir
    **şehir silueti** oluşuyordu. Sorun blokların şekli değil aralarındaki
    boşluktu. Ekranın tamamı kaya olunca sorun kayboldu. İkinci tuzak:
    orta katmanı en açık renk yapmıştım (abyss 46), göz onu arka plan
    değil **nesne** sanıyordu — üç kademe tek yönde koyulaşmalı.

20. **Çizilen her ışık kaynağı bir şeye bağlı olmalı.** Meşaleleri sabit
    bir satıra koymuştum; odaların tavan yüksekliği farklı olduğu için
    yarısı havada asılı kaldı. Artık her meşale kendi odasının tavanına
    göre yazılıyor ve test üstünde gerçekten tile var mı diye bakıyor.

21. **`Boss.draw_health_bar` vardı, hiçbir sahne çağırmıyordu.** "Sahne
    çağırır" diye yazılmış bir metot, çağıran taraf yazılmadığı sürece
    ölü koddur ve varlığı yanlış bir güven verir. Boss dövüşü barsız
    oynanıyordu ve bunu ancak ekran görüntüsüne bakınca fark ettim.

22. **Heredoc (`<<'EOF'`) Türkçe metin ve ters bölü ile güvenilmez.**
    Bu oturumda iki kez içeriği bozdu (`` → bell karakteri, kaçış
    dizileri). Uzun metin dosyalarını Write aracıyla yaz, kısa yamaları
    Python betiğiyle uygula.

23. **Yazılıp hiç çalıştırılmayan kod hatasız görünür, hatasız değildir.**
    `tileset.py` iki görev boyunca "yazıldı ama bağlanmadı" diye durdu;
    bağlanır bağlanmaz üç yerde var olmayan zincir adına başvurduğu
    ortaya çıktı (`"stone"`/`"danger"` zincir değil, ramp/renk adı).
    Bir modülün import edilebilir olması çalıştığı anlamına gelmez -
    `tools/shot.py` ile gerçek bir sahne çizdirmek şart.

24. **`elif` iki koşulu "ya biri ya öbürü" sanmak, ikisi aynı anda doğru
    olduğunda sessizce yanlış dalı seçtirebilir.** `Climber._think_hanging()`
    ilk halinde `if overhead and tokens.request(): tell` / `elif
    patient_drop: drop()` idi - pusu VE sabır aynı anda doğruyken (oda dolu,
    hak reddedildi) `elif` doğrudan tell'siz düşüşe düşüyordu; "Telegraf
    şart" kuralı (dosyanın kendi docstring'i) sessizce çiğneniyordu. Kural
    şuydu: iki koşul birbirini SAF DIŞI bırakmıyorsa (`overhead` VE
    `patient` aynı anda true olabiliyorsa), `elif` yerine iç içe `if` kur ki
    hangi dalın önceliği olduğu açıkça yazılsın.

25. **Bir sahnenin ihtiyacı için eklenen davranış, paylaşılan bir sınıfa
    global olarak eklenirse başka her çağıranı sessizce değiştirir.**
    Bölüm 1'in beat-zamanlayıcısı için `Dialogue`'a eklenen
    `AUTO_ADVANCE_HOLD_FRAMES` (tamamlanan replik 50 kare sonra
    kendiliğinden ilerler) ilk halde koşulsuzdu - Bölüm 2/3'ün etkileşimle
    tetiklenen repliklerini de (boss karşılaşması gibi) sessizce
    etkiliyordu, oysa onlar hiçbir zamanlayıcıyla yarışmıyor. Düzeltme:
    `start(..., auto_advance=False)` - varsayılan eski davranış, yalnızca
    ihtiyacı olan çağıran `True` geçiyor. Paylaşılan bir sınıfa "bir yer
    için" davranış eklerken varsayılanın eski davranışı koruyup korumadığı
    kontrol edilmeli.

---

## 5. MİMARİ — HIZLI HARİTA

```
src/
├── config.py          TÜM sayısal değerler, KARE cinsinden. Sihirli sayı yok.
├── core/
│   ├── game.py        Sabit 60 kare döngü, 480×270, tam sayı ölçekleme, hitstop
│   ├── scene.py       Sahne yığını (tek döngü kuralı — ikinci while ASLA)
│   ├── input.py       Aksiyon eşlemesi + 8 karelik tampon
│   ├── camera.py      Takip, ölü bölge, ileri bakış
│   └── juice.py       ★ on_hit() — hitstop+sarsıntı+parçacık TEK çağrıdan
├── art/
│   ├── palette.py     32 renk, tools/palette.json'dan okur. Palet dışı YASAK.
│   ├── forge.py       İndeks tabanlı çizim (renk değil, zincir+basamak)
│   ├── spritegen.py   draw_humanoid — tek iskelet, çok karakter
│   ├── animation.py   Poz üreticileri + karakter kütüphanesi
│   ├── animator.py    Oynatıcı + sprite önbelleği
│   ├── particles.py   Sütun tabanlı, üst sınır 200
│   └── tileset.py     ★ Görev 9 — prosedürel tuğla/kiriş, TileMap.draw() bağlı
├── combat/
│   ├── combo.py       3'lü zincir (chain_table silaha göre değişir), kaçınma, combo sayacı
│   ├── weapons.py     ★ yumruk/kılıç/hançer/balta kaydı — Player.equip_weapon()
│   ├── attack_token.py ★ aynı anda en fazla 2 saldırgan
│   └── hitbox.py      Kare bazlı hitbox — kimse doğrudan hasar vermez
├── entities/          actor · player · player_render · character_stats · dummy
│   ├── enemy.py       Durum makinesi, tell, poise — 10 tipe genişler
│   └── enemies/       shambler · climber · bloated
├── systems/           save (yedekli) · settings · echo · compass
│   ├── abilities.py   ★ Player.has() TEK kapı — yetenek kapısı dağıtılmaz
│   └── charms.py      Koşullu tılsımlar; çarpan vuruş ÜRETİLİRKEN biner
├── ui/                text (tr_upper!) · widgets · menu · character_select
│                      settings_scene · pause · hud · font_data
│   ├── i18n.py        t() — TR/EN, çizim anında çözülür
│   └── lang/          tr.json (kanonik) · en.json
├── world/             tilemap (16×16, ASCII) · decals (kalıcı izler)
│   ├── level.py       ASCII → zemin + yerleşim. join_rooms() odaları yan yana ekler
│   ├── pickups.py     Sandık — dokununca açılır, tuşa basınca değil
│   ├── cave_backdrop.py  Yeraltı arka planı, üç kaya kademesi (B2, B3, B5...)
│   └── rooms/         chapter01 · chapter02 — oda verisi, ASCII blok olarak
└── scenes/            combat_room · foundation_check · intro · menu_reveal
                       vertical_journey · cinematic · chapter01 · chapter02
    └── play.py        ★ PlayScene — bütün game feel kancaları BURADA
```

### Değiştirmeden önce bilinmesi gerekenler

- **Zaman birimi karedir.** `dt` yok. Hız piksel/kare, ivme piksel/kare².
- **Renkle değil, gölge zinciriyle çizilir.** `forge.Canvas` her piksel için
  (zincir, basamak) tutar; `shade()` ve `outline()` bunun üstünde çalışır.
- **Hasar tek yerden geçer.** `hitboxes.spawn(Hitbox(...))` → `HitboxManager`
  çözer → `scene.on_hit()` game feel'i verir. `take_damage` doğrudan çağrılmaz.
- **`smoothscale` yasak** (ışık/bulanıklık katmanı hariç).
- **400 satırı geçen dosya bölünür.** İki kez bölmek gerekti, gerekirse yine böl.
- **Türkçe:** yorumlar Türkçe, tanımlayıcılar İngilizce. Büyük harf için
  **her yerde** `text.tr_upper()` — `str.upper()` Türkçe'de yanlış.

---

## 6. AÇIK KALANLAR

Sıra gelmediği için değil, gözden kaçmasın diye burada:

1. **Ses sistemi yok.** `game.play_ui_sound()` çağrılıyor, gövdesi boş.
   `juice.pitch_variation()` hazır. Görev 10.
2. **Renk körü modu, parlaklık, arayüz ölçeği** ayarlarda görünüyor ama
   uygulanmıyor. Palet tek kaynak olduğu için renk körü ucuz.
   (Dil ayarı artık **çalışıyor** — TR/EN, anında geçiş.)
3. **Ardo'nun oynanışı Rey'in aynısı** — sayılar farklı, İz Sürme mekaniği
   (`docs/derinlestirme.md` 2.4) yok.
4. ~~**Tileset placeholder.**~~ ✅ (22.08.2026) `world/tilemap.py` artık
   `src/art/tileset.py`'den prosedürel tuğla/kiriş dokusu blit ediyor (duvar
   4 varyant, platform 2 varyant, diken). Gerçek 9-slice (köşe/kenar ayrı
   parça) hâlâ yok - şu an "üstü açık mı" tek ekseninde iki hal var, bu
   odaların dikdörtgen blok tasarımı için yeterli görünüyor; köşe
   karmaşası gerekirse ayrı bir iş.
5. **EKSTRALAR ve EKİPMAN menüde kapalı** — içerikleri sonraki görevlerde.
6. **`docs/asset-plani.md` güncel değil:** "Türkçe karakter eksik" ve
   "prototipteki sprite kalitesi" maddeleri artık geçersiz.
7. **`_prototype/` içinde işe yarar kod var** — parallax, ışıklandırma,
   post-fx, tile üreteci. Referans olarak bak, **asla import etme.**
8. **`game.music_hush` dolduruluyor ama kimse okumuyor.** Bölüm 2 gizli
   odacığa girince 0→1 yükseltiyor; görsel yarısı (kenarlardan içeri çekilen
   karanlık) çalışıyor, müziği kısacak taraf Görev 10'da yazılacak.
9. **Bölüm 2'nin ödülünde eksik var:** belge mini-boss sonrası **ilk silah
   seçimi** (Hançer / Balta) veriyor. Şu an sadece 55 altın veriliyor.
   Silah **altyapısı** artık var (`src/combat/weapons.py`, §2 madde 10) —
   `DAGGER`/`AXE` tanımlı, ama hiçbir sahne henüz vermiyor. Eksik olan
   tamamen **içerik/akış**: mini-boss sonrası seçim ekranı, `SaveData`'ya
   hangi silahın seçildiğinin yazılması, Hançer/Balta'nın kendi sprite'ı.
10. **Checkpoint yok.** Oyuncu ölünce sahne yeniden kurulmuyor; Bölüm 2'de
   arena kapısı ölümde açılıyor ki oyuncu kilitli kalmasın, ama gerçek
   çözüm bir yeniden doğma sistemi. Bölüm 3'te de aynı durum.
11. ~~**Marooned dusman kendiliginden asagi inmiyor.**~~ ✅ (22-23.08.2026,
   DÖRT AYRI TUR — dördüncüsü 23.08.2026, henüz commit'lenmedi, bkz. §4
   madde 24) `_vertically_reachable()` (commit `c812bbb`) erişilemez bir
   hedefe saldırı denemesini durdurmuştu ama düşman yüksek/kopuk bir
   platformda sonsuza kadar bekleyebiliyordu - Arda ekran görüntüsüyle
   "hâlâ yapışık" diye bildirdi (iki kere, iki farklı ekran görüntüsüyle).
   Üç kademede tam düzeltildi:
   1) `ENEMY_UNREACHABLE_PATIENCE_FRAMES` sonrası `_nearest_ledge_direction()`
      ile en yakın kenarı bulup düşme eklendi; `Climber`'ın ayrı
      asılı-bekleme mekanizması `CLIMBER_PATIENCE_FRAMES` ile aynı fikri
      aldı.
   2) `Climber.aware_frames` sayacı `self.aware`'e bağlıydı - `aware`
      yalnızca YATAY mesafeye bakıyor, oyuncu hiç yatay olarak
      yaklaşmazsa (örn. başka bir platformdan geçerse) sayaç hiç
      başlamıyordu. Koşulsuz sayıma çevrildi.
   3) **Asıl kalan hata (Arda'nın "hâlâ yukarıda" bildirdiği üçüncü tur):**
      hem genel `Enemy._approach()` hem `Climber`'ın sabır-düşüşü,
      düşmenin kendisini saldırı hakkı (`AttackTokenManager`, aynı anda
      en fazla 2) alabilmeye bağlıyordu. Bir odada 2'den fazla düşman
      varsa (ekran görüntüsündeki 4 düşman gibi) hak sürekli
      başkalarında kalabiliyor ve "sabır" hiçbir şey garanti etmiyordu.
      Ayrıca genel sayaç yalnızca düşman zaten `APPROACH` durumundaysa
      (yani hem farkında HEM hakkı varsa) işliyordu - hiç farkına
      varmayan bir düşman sayacı hiç başlatamıyordu. Düzeltme: (a)
      erişilebilirlik artık farkındalıktan bağımsız her karede ölçülüyor
      (`Enemy._update_reachability()`), sabır dolunca IDLE/ORBIT
      durumunda bile kenar aranıyor; (b) `Climber`'ın sabır-düşüşü artık
      saldırı hakkı GEREKTİRMİYOR - yalnızca gerçek pusu (oyuncu tam
      altında) hak istiyor, sabır düşüşü doğrudan `_drop()`. İki yeni
      regresyon testi (`tests/test_enemy.py`: sahte "hak hiç verilmiyor"
      yöneticisi + "hiç farkına varmadan" senaryosu) bunu kanıtlıyor.
   4) **Dördüncü tur (23.08.2026) - başka bir Claude oturumu 3'ü uygulamış
      ama commit'lememişti; bu oturum kod incelemesinden iki gerçek hata
      daha buldu ve düzeltti:**
      - `Climber._think_hanging()`'te pusu (`overhead_player`) VE sabır
        (`patient_drop`) aynı anda doğruyken hak reddedilirse (oda dolu),
        `elif patient_drop: self._drop()` dalı tell'siz doğrudan
        düşürüyordu - tam da bu dosyanın kendi "Telegraf şart" kuralını
        kırıyordu. Düzeltme: `patient_drop` artık yalnızca `overhead_player`
        YANLIŞKEN devreye giriyor; pusu varken hak açılana kadar tell
        denemeye devam ediyor, asla habersiz düşmüyor.
      - `Enemy._try_escape_unreachable()` (genelleştirilmiş kaçış, madde 3'ün
        (a) şıkkı) `_face_player()` çağrılmadan önce çalışıyordu - hiç
        farkına varmamış bir düşman için `self.facing` o karede hiç
        güncellenmemiş/bayat olabiliyordu, `_nearest_ledge_direction()` de
        önce `facing` yönünü denediği için yanlış kenara yönelebiliyordu.
        Düzeltme: kenar aramadan önce `_face_player()` eklendi.
      İki yeni regresyon testi hâlâ yeşil, `tools/reachability.py` da öyle.
      Ayrıca bu turda `enemy.py` 384 satırdan 400 sınırının üstüne çıkmıştı
      (yeni `_update_reachability`/`_try_escape_unreachable`) - dikey
      erişim/kenar-arama mantığı `src/entities/enemy_navigation.py`'ye
      taşındı (serbest fonksiyonlar, `enemy_render.py`'deki
      `draw_enemy(enemy, ...)` deseniyle aynı - circular import açmıyor).
      Kullanılmayan `Enemy.body_tint()` da bu geçişte silindi (hiçbir yerden
      çağrılmıyordu, `enemy_render.py::_tint()` aynı mantığı zaten
      bağımsız tekrarlıyordu - CLAUDE.md 4/23'teki "çalıştırılmayan kod"
      dersine tam örnek). Bölünme sırasında bir tane daha aynı türde hata
      eklendi ve otomatik bir inceleme turu tarafından hemen yakalandı:
      `_try_escape_unreachable()`, `enemy_navigation.py`'deki serbest
      `nearest_ledge_direction(enemy)` fonksiyonunu **doğrudan** çağırıyor -
      `Enemy._nearest_ledge_direction()` sarmalayıcı metodu hiçbir yerden
      çağrılmıyordu, silindi.
      Ayrı bir hata daha bu turda bulundu: prolog diyalog düzeltmesi
      (`AUTO_ADVANCE_HOLD_FRAMES`, aşağıdaki madde 13) `Dialogue` sınıfının
      TAMAMINA uygulanmıştı - Bölüm 2/3'ün etkileşimle tetiklenen (boss
      karşılaşması, gizli duvar vb.) replikleri de oyuncu onaylamasa 50
      kare sonra kendiliğinden kapanır hâle gelmişti. `Dialogue.start()`'a
      `auto_advance: bool = False` parametresi eklendi; yalnızca Bölüm 1'in
      beat-zamanlayıcısıyla yarışan repliklerde `True` geçiliyor, diğer
      tüm `say()` çağrıları eski (onaylanana kadar ekranda kalan) davranışta.
13. **Bölüm 1 prologunda pasif oyuncu repliği kaybediyordu (23.08.2026,
   commit'lenmemiş bir oturumdan devralındı, bu oturumda tamamlandı).**
   Çok-replikli bir beat'te ("gift": Cemo + Rey) ikinci satır onayla
   geçilmediği sürece beat süresi dolunca `_on_beat_start()` kuyruğu
   **sessizce** değiştiriyordu - Arda'nın "bunlar çok anlamsız cümleler"
   geri bildirimi bunun sonucuydu. İki parçalı çözüm: `chapter01.py`'de
   `DIALOGUE_GRACE_FRAMES=100` - beat, diyalog bitene kadar (üst sınırla)
   bekler; `dialogue.py`'de `auto_advance=True` ile başlatılan diziler
   tamamlandıktan `AUTO_ADVANCE_HOLD_FRAMES=50` kare sonra kendiliğinden
   ilerler (pasif oyuncu için). `tests/test_chapter01.py`'e hiç girdi
   vermeden tüm prologu oynatıp 5 repliğin de göründüğünü doğrulayan bir
   regresyon testi eklendi. **Kapsam bilerek dar tutuldu** - bkz. madde
   12'nin son paragrafı: yalnızca beat'e bağlı replikler `auto_advance`
   alıyor, kesif/dövüş repliği eski davranışta kalıyor.
14. **Bölüm 3'ün "5 yuva" ödülü basitleştirildi.** `docs/bolum-03.md`
   yuvaların hepsi yanınca "ısıyla açılan bir gizli kapı" tarif ediyor;
   kodda bulmaca çözümü sadece bir kutlama efekti/toast veriyor, Mum
   Bekçisi'nin cebi ayrı, her zaman kılıçla kırılabilir bir duvarın
   ardında (diğer gizli duvarlarla aynı dil). Bilinçli bir sadeleştirme -
   DEVIR.md'de not düşüldü ki "neden farklı" sorusu sorulunca cevap hazır
   olsun.
15. **İki gerçek, ÖNCEDEN COMMIT'LENMİŞ hata daha bulundu ve düzeltildi
   (23.08.2026) - bu oturumun asıl görevi değildi (Bölüm 1/enemy fix'ini
   bitirmekti) ama otomatik bir kod inceleme turu bunları Bölüm 3'ün
   kendi kapsamında yakaladı, ikisi de "dikey dilim" değerlendirmesini
   etkileyecek kadar ciddiydi:**
   - **`Climber._think_hanging()`'te `_fleeing_light` STAGGER/TELL
     kontrolünden ÖNCE `return` ediyordu** (Bölüm 3 Oda 3'ün "ışıktan
     kaçar" mekaniği - madde 11'in üçüncü şıkkı ile aynı fonksiyon, farklı
     dal). Işık alanı içinde vurulan bir Tirmanan, "yukarıda kalıp
     sıkışmasın" diye var olan STAGGER-de-anında-düşme garantisini
     kaçırıp sabır eşiğine kadar (150 kare) asılı kalabiliyordu. Düzeltme:
     STAGGER ve TELL kontrolleri artık `_fleeing_light`'tan ÖNCE - vurulmuş
     ya da saldırı dizisinde olmak kaçıştan her zaman öncelikli.
   - **`ExtinguishedOne._think()`, "sürükleme" hamlesinin ATTACK durumunda
     `super()._think()`'i HİÇ çağırmadan dönüyordu** (`if state is ATTACK
     and move=="drag": return`). Tabanın ATTACK dalının yaptığı iki şey -
     hitbox'ı açan `_spawn_attack()` ve `active_frames` sonrası RECOVER'a
     geçiş - hiçbir zaman çalışmıyordu. `MOVES` dizisinde "sürükleme" iki
     kez var (4 hamlenin 2'si) - boss'un ilk birkaç saldırısından biri
     kaçınılmaz olarak bu hamleye denk gelip ATTACK'ta **sonsuza dek**
     kilitleniyordu (hiçbir hasar vermeden, hiçbir yere geçmeden) - mini-boss
     dövüşü tamamen oynanmaz hale geliyordu. Kontrol edildi: dövüşün kendi
     override'ının gerekçesi ("_think normalde vx'i yaklaştırırdı") artık
     yanlıştı - tabanın ATTACK dalı vx'e hiç dokunmuyor (yalnızca RECOVER
     dokunuyor) - override muhtemelen taban değiştikten sonra bayatlamıştı.
     Düzeltme: gereksiz/zararlı override tamamen silindi.
   `tests/test_enemy.py`'e her ikisi için de regresyon testi eklendi
   (ışıktan kaçarken vurulma → anında düşme; sürükleme hamlesi → hitbox
   gerçekten açılıyor VE ATTACK'ta kilitlenmiyor). `test_chapter03.py`'nin
   40 kontrolü bu iki senaryoyu hiç kapsamıyordu (boss'un "sürükleme"
   hamlesini hiç tetiklemiyordu) - otomatik inceleme olmasa muhtemelen
   Arda'nın kendi oynanış turunda bulunacaktı. On üç test paketi + 
   `tools/reachability.py` hâlâ yeşil.

---

## 7. GİT DURUMU — **BAŞKA BİLGİSAYARA GEÇERKEN ÖNCE BURAYI OKU**

**v3 artık `main`.** 22.08.2026'da `v3-yeniden-yapilandirma` dalı
fast-forward ile main'e alındı ve push edildi. İkisi de aynı commit'te
duruyor; v3 dalı silinmedi ama artık main'den farkı yok.

Uzak depo: `https://github.com/Ardeko/Legend-Of-Rey.git`

**Eski motor `v2.1` etiketinde:** `git checkout v2.1` ile v3 öncesine
dönülebilir. main'in geçmişinde ata commit olarak duruyor, kaybolmadı.

> ### Diğer bilgisayarda
>
> ```bash
> git clone https://github.com/Ardeko/Legend-Of-Rey.git
> cd Legend-Of-Rey
> python -m venv .venv
> .venv/Scripts/activate           # Windows (Git Bash)
> pip install pygame-ce numpy
> python main.py                   # intro'dan başlar
> ```
>
> Dal değiştirmene gerek yok, `main` doğru yer.
> `.venv/` ve `build/` klonlanmaz, ikisi de yeniden üretilebilir.
>
> **İki makinede çalışırken:** başlamadan `git pull`, bitirince `git push`.
> Unutulursa dallar ayrışır ve birleştirmek zahmetli olur.

Commit mesajları **niçin** öyle yapıldığını anlatıyor — bir davranışı
değiştirmeden önce ilgili commit'e bakmakta fayda var. Son commit:

```
Bolum 2 - Ilk Inis: 8 oda, gizli odacik, mini-boss, bolum sonu ekrani
```

Bir şey ters giderse: **commit'lenmiş hiçbir şey kaybolmaz.**
`git log --oneline --all` bütün dalları, `git reflog` ise nereye
gidildiğini gösterir. Yanlış dala geçmek veri kaybı değildir —
`git status` temizse `git checkout main` her şeyi geri getirir.

---

## 8. SIRADAKİ ADIM

**Görev 8 tamamlandı** (22.08.2026) — Bölüm 3 "Meşale Mahzeni" baştan sona
oynanabilir: ışık sistemi (`src/systems/light.py` + `src/art/lighting.py`),
taşınabilir meşale (`src/world/torch.py`), ses haritası/sonar
(`EchoState.pulse()`), Gölge Sürüklenen (`shadow_shambler.py`), Mum
Bekçisi ticareti (`candle_keeper.py` + `systems/economy.py`), Mor Alev
kararı, mini-boss "Sönmüş Olan" (mangal mekaniği). `tests/test_chapter03.py`
(40 kontrol) + `tools/reachability.py` yeşil.

Arda uzun süre bilgisayar başında olmayacağı için **tam yetki verdi**
(bkz. §2 madde 8) — onay beklemeden ilerleniyor. Sırayla:

1. ~~**Görev 5 — Ara Değerlendirme.**~~ Arda'nın kendi oturup oynaması
   gereken adım; o yokken atlanıyor, geri döndüğünde kendisi karar verir.
2. ~~**Düşmanların üst platform/çatılara sıkışması**~~ ✅ (commit
   `c812bbb`). Kök neden: `Enemy._approach()` saldırı kararını yalnızca
   yatay mesafeye bakarak veriyordu; oyuncu tam altındaysa dikeyde
   erişilemez bir hedefe sonsuza dek TELL/ATTACK deniyordu.
   `_vertically_reachable()` eklendi. **Açık kalan yarım:** dusman hala
   platformdan kendiliğinden inip savaşa dönmüyor (sadece artık boşuna
   saldırmıyor) - ledge-detection gerektiren ayrı, daha büyük bir iş,
   bilerek kapsam dışı bırakıldı.
2b. ~~**Ardo, Bölüm 1'de anlamsız bir "Yankı Görüşü kazandın" bildirimi
   görüyordu**~~ ✅ (commit `03d34ac`). `on_echo_tutorial()` artık
   `self.echo is None` iken (Ardo) hemen dönüyor.
2c. ~~**Mini-boss arenasının kapısı oyuncunun yüzüne kapanıyordu**~~ ✅
   (commit `03d34ac`). Kapı artık oda sınırına girer girmez değil,
   oyuncu kapı sütununu gerçekten geçince kapanıyor. İlk deneme yeni bir
   hata doğurdu (kapı açılınca kendini hemen yeniden kilitliyordu),
   `boss_defeated` bayrağıyla çözüldü - `tests/test_chapter02.py`'ye
   regresyon kontrolü eklendi.
2d. ~~**Silah sistemi altyapısı**~~ ✅ (commit sonrası). Arda'nın isteği:
   yumrukla başla, kılıcı sonra bul; Hançer/Balta/gelecekte menzilli için
   mimari hazır ama içerik yazılmadı. Detay §2 madde 10.
3. ~~**Görev 9 — Tileset bağlama.**~~ ✅ `src/art/tileset.py` artık
   `world/tilemap.py::_draw_tile`'a bağlı - duvar/platform/diken düz renk
   değil, prosedürel doku (`tools/shot.py` ile 3 sahnede görsel doğrulandı,
   Bölüm 3'ün karartma maskesi altında da doğru görünüyor). Bağlanırken
   çıkan gerçek hata ve düzeltmesi: §2 madde 11, §4 madde 23. Kalan:
   gerçek 9-slice köşe/kenar ayrımı yok (şimdilik gerek görülmedi) ve
   asıl "Görev 9" başlığının geri kalanı - **ses** hâlâ yazılmadı.
4. ~~**Görev 10 — Ses (öncelik 1 seti).**~~ 🟡 (22.08.2026) Gerçek kayıt
   yok - `src/audio/` altında numpy ile **sentezlendi** (CLAUDE.md 6'nın
   sprite ilkesiyle aynı gerekçe: kod ile üret). `synth.py` (osilatör/
   zarf/filtre), `sfx_combat/world/enemies/ui.py` (~50 ses üretici),
   `mixer.py` (oynatma, hacim, ★ bogulma seti, perde varyasyonu, dongu
   yönetimi). `game.play_sound()`/`play_loop()`/`stop_loop()` ile TÜM
   sahnelere bağlandı - vuruş, adım, zıplama/iniş, kaçınma, Yankı ac/kapa/
   soru-cevap, kolye kalp atışı, düşman tell/ölüm, sandık, meşale, menü,
   intro, dikey yolculuk (rüzgar/mahzen çaprazlaması). Arda canlı
   oynanışta hemen geri bildirim verdi ve **aynı oturumda düzeltildi**
   (§2 madde 12): kare dalga → sinüs, adım sesi sıklığı 5x azaltıldı,
   genel ses tepe seviyesi düşürüldü. Kalan: müzik (bölüm 9) ve öncelik
   2-3 setleri hâlâ yok.
5. ~~**İkinci canlı oynanış turu (22.08.2026) — altı ayrı geri bildirim,
   hepsi aynı oturumda çözüldü:**~~ ✅
   - **Düşmanlar hâlâ yukarıda/tavanda "yapışık" kalıyordu** (ekran
     görüntüsüyle bildirildi) - madde 2'nin "açık kalan yarımı" buydu.
     `Enemy._approach()` artık `ENEMY_UNREACHABLE_PATIENCE_FRAMES` (90
     kare) sonra en yakın kenarı arayıp (`_nearest_ledge_direction`)
     düşüyor; `Climber`'ın kendi ayrı asılı-bekleme mekanizması da aynı
     hataya sahipti, `CLIMBER_PATIENCE_FRAMES` (150 kare) ile o da
     düzeltildi.
   - **"Mini-boss duvarına sıkışıyoruz"** (ekran görüntüsü) - araştırma
     sonucu: Bölüm 2'nin kapısı doğru çalışıyor (bot-yürüyüş testiyle
     doğrulandı, boss görünür olduktan uzun süre sonra kapanıyor), oda
     geometrisinde de engel yok. Kapı **kasıtlı/gerçek** bir mühür -
     ama sessizce beliriyordu, oyuncu "az önce bir şey oldu" değil
     "burada hep bir duvar varmış" hissediyordu. `rift_close` sesi
     eklendi.
   - **"Sesler çizirti gibi, kaldıralım"** - sentezlenmiş TÜM donguluk
     (loop) sesler kaldırıldı (karakter seçim fısıltısı, Yankı açıkken
     sürekli ses, üç bölümün ortam döngüleri, intro uğultusu, dikey
     yolculuk rüzgâr/mahzen çaprazlaması). Kısa tek seferlik efektler
     (vuruş/adım/UI) kaldı - ayrı, olumsuz geri bildirim almadılar.
   - **"Kaçınma/sprint geldiğini söyleyen ipucu yok"** - `on_ability_gained()`
     paylaşılan `PlayScene`'e taşındı, Bölüm 2 artık kaçınmayı
     `if grant(): on_ability_gained()` ile açıkça bildiriyor (eskiden
     sessizce veriliyordu).
   - **"Ardo kafasındaki şey yüzünden yaratığa benziyor"** - kukulete
     tamamen kaldırıldı, tam açık yüz + gümüş/gri kısa saç. Detay §2
     madde 13.
   - **"Ayarlar sekmesi kötü, Ses'e gitmek için en aşağı inmek gerekiyor"**
     - `Action.NEXT_TAB` (Tab/RB) + fare tıklama ile sekmeler arası
     doğrudan geçiş, tab şeridi + seçili satır + ok işaretleri görsel
     olarak yenilendi.
   - **Ek istek:** C&C tarzı özel altın imleç (`src/ui/cursor.py`) -
     OS oku artık hiç görünmüyor.

   Tüm değişiklikler ayrı commit'ler halinde, her biri kendi regresyon
   testiyle. 13 test paketi + `tools/reachability.py` her adımda yeşil
   kaldı.

6. ~~**Üçüncü canlı oynanış turu (22-23.08.2026) — ekran görüntüleriyle
   bildirilen iki hata + referans karakter görselleri:**~~ ✅
   - **KRİTİK — mini-boss kapısı kapanırken oyuncuyu gövdesinin içinde
     bırakabiliyordu** (commit `feeab53`). Bölüm 2/3'ün arena-kapısı
     mühürleme eşiği `player.body.center_x` (gövde MERKEZİ) kullanıyordu;
     gövdenin genişliği yüzünden merkez eşiği geçtiği ama sol yarısının
     hâlâ mühürlenecek sütunla çakıştığı gerçek bir kare penceresi vardı -
     tam o karede mühürleme tetiklenirse oyuncu katı geometrinin içinde,
     hiçbir kaçış yönü olmadan sıkışıp kalıyordu. Doğrudan benzetimle
     doğrulandı (eski formülün mühürleyeceği karede `overlap=True`).
     Düzeltme: eşik `player.body.x` (SOL kenar) oldu - gövdenin TAMAMI
     sütunu geçmeden mühürlenmiyor. Hem Bölüm 2 hem Bölüm 3 aynı deseni
     kullanıyordu, ikisi de düzeltildi. Yeni bir "kapıya yürüyerek gömülme"
     regresyon testi eklendi - ilk testler `teleport()` tabanlıydı ve bu
     hatayı hiç yakalamamıştı (o kare penceresini atlıyordu) - ders:
     gerçekten yürünen senaryoyu test et, yalnızca ışınlanmayı değil.
   - **Ardo'nun oyun başında zaten silahlıyken yerde ikinci bir kılıç
     prop'u görünmesi** (commit `07da0bb`) - `Chapter01Scene.setup()`
     `sword_pos`'u karaktere bakmadan dolduruyordu. Artık Ardo için
     baştan `None`.
   - **Ardo'nun görünümü** (referans karakter görselleri + "havalı ve
     yakışıklı" tarifi üzerine) - ayrı kürk tonlu omuz zırhı + saç rengi
     Rey'le aynı koyu tona çekildi. Detay §2 madde 13 (üçüncü tur).
   - **Düşmanlar hâlâ tavanda/yukarıda yapışık kalıyordu** (madde 5'in
     "düzeltildi" dediği hata **tam çözülmemiş** çıktı - saldırı hakkı
     kıtlığı sabrı da etkiliyordu) + **Bölüm 1 prologunda replik
     kayboluyordu** ("bunlar çok anlamsız cümleler") + **Sönmüş Olan
     boss'unun "sürükleme" hamlesi ATTACK'ta sonsuza kilitlenebiliyordu**
     (üçü de birden fazla Claude oturumunun art arda incelemesiyle
     bulundu/düzeltildi). Tam detay §6 madde 11 (4 tur), madde 13, madde 15.

   Sırasıyla 22.08 ve 23.08 tarihli commit'ler halinde, hepsi kendi
   regresyon testiyle. On üç test paketi + `tools/reachability.py` bu
   turun sonunda da yeşil.

Arda geri döndüğünde sırayı değiştirebilir — daha önce iki kez değiştirdi.

**Not: `git push` bu ortamda çalışmıyor** (kimlik doğrulama yok -
`fatal: could not read Username for 'https://github.com'`). Commit'ler
yerelde birikiyor; başka bir makineden ya da kimlik bilgisi girilen bir
oturumdan `git push` çalıştırılması gerekiyor.

---

## 9. ÇALIŞMA DÜZENİ (CLAUDE.md §13 özeti)

1. Görevi oku, `docs/` içinden ilgili belgeyi aç
2. Büyük görevde **önce plan sun**, onay al
3. Kodu yaz
4. **Çalıştır ve kanıt göster** — test çıktısı, komut, ekran görüntüsü
5. Ne yaptığını özetle, açık kalanları söyle
6. **Önerilerini listele**
7. **Dur.** Sıradaki göreve kendiliğinden geçme.

Sandbox'ta çalışmayan bir adım varsa görevi "tamamlandı" ilan etme.
