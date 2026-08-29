# DEVİR — Legend of Rey (LORE)

**Bu proje hakkında tek devir belgesi budur.** Başka bir AI oturumuna
devredildiğinde okunması gereken tek dosya.

Okuma sırası: **1) `CLAUDE.md`** (bağlayıcı kurallar — anayasa) → **2) bu
dosya** (nerede kaldık) → 3) gerekirse `docs/` altındaki ilgili tasarım
belgesi.

Son güncelleme: **29.08.2026** (Faz A–G tamamlandı) · Ardeko Studios · Arda Güner

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

**~19.100 satır Python. 13 test paketi de yeşil.**

Oynanabilir akış:
`intro → menü → karakter seçimi → dikey yolculuk → **Bölüm 1 (Köy)** →
**Bölüm 2 (İlk İniş)** → bölüm sonu ekranı → **Bölüm 3 (Meşale Mahzeni)**
→ bölüm sonu ekranı → ana menü`

Bölüm 3'ün sonu ana menüye dönüyor çünkü **Bölüm 4 henüz yok** — bilinçli
bir uç.

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
| **1 — Çürüyenler** | B1–B6 | combo **kurmayı** | Sürüklenen, Tırmanan, Şişmek | ✅ sanat + AI |
| **2 — Lanetli Muhafızlar** | B7–B13 | combo'yu **kırmayı** | Kalkanlı, Mızraklı, Okçu, Komutan | 🟡 sanat var, **AI yok** |
| **3 — Yankı'nın Çocukları** | B14–B18 | yardımcının ihaneti | Sessiz, Yankılayan, Bölünen | 🟡 sanat var, **AI yok** |

Artı **4 büyük boss** (B6, B13, B14, B18) ve her bölümde bir mini-boss
("mevcut düşmanın büyütülmüş hâli, bir ek hamle" — bilinçli olarak ucuz).
Yapılan mini-boss'lar: Şişmiş Olan (B2), Sönmüş Olan (B3).

---

## 9. AÇIK KALANLAR

Sırası gelmediği için değil, **gözden kaçmasın** diye:

1. **Işık sistemi yalnızca Bölüm 3'e bağlı.** B1'in yarığı ve B2'nin
   meşaleleri gerçek ışık vermiyor. (Faz C'nin yarım kalan parçası.)
2. **Katman 2 ve 3'ün düşman AI'ları yok** — sadece sprite'ları var.
3. **Ardo'nun oynanışı Rey'in aynısı** — sayılar farklı, İz Sürme
   mekaniği (`docs/derinlestirme.md` §2.4) yok.
4. **Ardo'nun Bölüm 1'deki motivasyonu yazılmadı** (bkz. §3 madde 7).
5. **Boss kapısı + anahtar (24.08.2026)** — `src/world/keydoor.py`.
   Bölüm 2 ve 3'ün arena çıkışı kilitli, boss ölünce anahtar düşüyor.
   Aynı yapı sonraki boss odalarında da kullanılmalı; Bölüm 2/3'e
   bakarak bağlanır (`_drop_key` / `_update_key`).

6. **Bölüm 2'nin ödülü eksik:** belge mini-boss sonrası **ilk silah
   seçimi** (Hançer/Balta) veriyor, şu an sadece 55 altın. Altyapı hazır
   (`src/combat/weapons.py`), eksik olan **içerik/akış**: seçim ekranı,
   kayda yazma, Hançer/Balta sprite'ları.
6. **Checkpoint yok.** Oyuncu ölünce sahne yeniden kurulmuyor. Arena
   kapısı ölümde açılıyor ki oyuncu kilitli kalmasın, ama gerçek çözüm
   bir yeniden doğma sistemi.
7. **Müzik yok.** Ses efektleri var (sentezlenmiş). **Döngülü/sürekli
   sesler bilerek kaldırıldı** — Arda: *"cızırtı gibi, rahatsız edici"*.
   Altyapı (`play_loop`/`stop_loop`) duruyor, kullanılmıyor. Gerçek kayıt
   gelirse tekrar açılabilir.
8. **`game.music_hush` dolduruluyor ama kimse okumuyor.** Görsel yarısı
   çalışıyor, müziği kısacak taraf müzik gelince yazılacak.
9. **EKSTRALAR ve EKİPMAN menüde kapalı.**
10. **Bölüm 3'ün "5 yuva" ödülü basitleştirildi** — belge "ısıyla açılan
    gizli kapı" tarif ediyor, kodda kutlama efekti/toast var.
11. **Gerçek 9-slice tileset yok** (köşe/kenar ayrı parça). Şu anki
    dikdörtgen blok tasarımı için yeterli görünüyor.
12. **`docs/asset-plani.md` güncel değil** — "Türkçe karakter eksik" ve
    "prototipteki sprite kalitesi" maddeleri artık geçersiz.
13. **`_prototype/` referans, ASLA import etme.** İçinde işe yarar
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
  düşman AI'ları (4 bağımsız dosya), Bölüm 4 (yetenek ağacı ekranı),
  Bölüm 5 (su mekaniği), Bölüm 6 (team-up + ilk büyük boss), 18 bölüm
  bittikten sonra bütünsel denge geçişi.
- Bu projede fan-out'un gerçek riski var: her alt-ajan **soğuk başlıyor**
  ve bu repo bağlayıcı geleneklerle dolu (37 renk paleti, zincir-adı
  tuzağı, Türkçe yorumlar, kare tabanlı zamanlama, sıra kuralı). Bağlam
  kaybı bu projedeki hataların ana kaynağı oldu.
