# CLAUDE.md — Legend of Rey (LORE)

Bu dosya, bu repoda çalışan Claude Code için bağlayıcı kurallardır. Her oturumda önce bunu, sonra `docs/` altındaki ilgili belgeyi oku.

---

## 1. PROJE

**Legend of Rey (LORE)** — Pygame ile yapılan, yandan görünümlü aksiyon-RPG.
Kafasının içindeki sesler yüzünden lanetli sayılan Rey, kaçırılan kardeşi Cemo'yu kurtarmak için zindana iner — ve o sesler ona yardım ederken, aslında onu çağırıyordur.

**Stüdyo:** Ardeko Studios
**Hedef platform:** PC (klavye + gamepad). **Mobil DEĞİL.**
**Kapsam:** 18 bölüm, ~4 saat, 2 oynanabilir karakter

---

## 2. TASARIM BELGELERİ

`docs/` altında. **Tamamını okuyabilirsin, hepsi bağlayıcıdır:**

| Dosya | İçerik |
|---|---|
| `docs/gdd.md` | Ana tasarım belgesi — sistemler, karakterler, bölüm listesi |
| `docs/dovus-sistemi.md` | Dövüş, combo, game feel, kare değerleri |
| `docs/ekonomi-uretim.md` | Altın, zorluk eğrisi, üretim aşamaları |
| `docs/asset-plani.md` | Asset listesi, stil kuralları, tutarlılık protokolü |
| `docs/bolum-02.md` | Dikey dilim — Bölüm 2 oda oda tasarım |
| `docs/bolum-03.md` | Bölüm 3 — Meşale Mahzeni, mor alev, Mum Bekçisi |

**Durum ve devir bilgisi `DEVIR.md`'de** (tek devir belgesi — `GOREVLER.md` 23.08.2026'da silindi).
| `docs/menu-ui.md` | Ana menü, karakter seçimi, ayarlar, HUD, UX prensipleri |
| `docs/yapi.md` | 18 bölümün tam akışı |
| `docs/derinlestirme.md` | Araştırma temelli ekler — ileri game feel, yenilikçi mekanikler, erişilebilirlik, Pygame performans |
| `docs/asset-listesi.md` | Kalem kalem asset dökümü — kaç kare, hangi boyut |
| `docs/asset-boru-hatti.md` | Asset üretim araçları — Pillow/NumPy boru hattı, quantize, siluet testi |

---

## 3. KAPSAM: MİMARİ SERBEST, İÇERİK SIRALI

Belgeler tüm oyunu anlatır ki **mimariyi geleceğe hazır kurabilesin**. Kurallar:

**Serbest — izin sorma:**
- Görev için gerekli olan her şeyi yaz
- Mimariyi geleceğe hazır kur; altyapıyı geniş tasarla
- Gerekli gördüğün yardımcı modülleri, arayüzleri, soyutlamaları oluştur
- Bir sistemi doğru kurmak için komşu sisteme kanca gerekiyorsa yaz

**Sıraya bağlı — sırası gelmeden yazma:**
- İleri bölümlerin **içeriği**: odaları, level verileri, düşman tipleri, boss'ları, ara sahneleri
- Bunlar oynanış test edilmeden yazılırsa, test sonrası değişikliklerde çöpe gider

**Görev bitince:**
Gördüğün eksikleri, iyileştirme fikirlerini ve dikkatini çeken sorunları **liste halinde öner**. Kullanıcı karar versin.

Kısacası: sistem altyapısında özgürsün, içerik üretiminde sıralısın.

---

## 4. TEKNİK STANDARTLAR

| Karar | Değer | Neden |
|---|---|---|
| İç çözünürlük | 480×270 | 16:9, tam sayı ölçekleme (2×,3×,4×) |
| Karakter | 32×32 | |
| Tile | 16×16 | |
| Kare hızı | **Sabit 60 FPS** | Dövüş kare hassasiyeti |
| Fizik adımı | **Sabit** | Değişken adım combo penceresini bozar |
| Zaman birimi | **Kare (frame)**, saniye değil | Tüm dövüş değerleri karede |
| Kayıt formatı | JSON | |
| Python | 3.11+ | |
| Bağımlılık | `pygame-ce` + `numpy` | Başka kütüphane ekleme, önce sor |

> **numpy onaylandı (21.08.2026).** Hem `tools/` boru hattında (quantize, shade,
> outline — bu belgenin kendi önerisi) hem de çalışma zamanında (parçacık
> alanı, ışık maskesi, tilemap) kullanılıyor. Parçacıkları saf Python'da
> güncellemek kare bütçesini yiyordu. Üçüncü bir kütüphane hâlâ izne tabi.

**Ölçekleme:** Her şey 480×270 yüzeye çizilir, sonra ekrana `pygame.transform.scale` ile büyütülür. `smoothscale` KULLANMA — piksel art bulanıklaşır.

### Performans kuralları (zorunlu)
- Yüklenen/üretilen **her yüzeyde** `.convert()` veya `.convert_alpha()` çağır. Unutulursa oyun 3-5 kat yavaşlar.
- Çarpışma için **alt-dikdörtgen** kullan: hitbox sprite'tan küçük olsun. Piksel-mükemmel çarpışma yapma — hem yavaş hem gereksiz, ayrıca küçük hitbox oyuncu lehine affedicilik sağlar.
- Sprite'lar başlangıçta **bir kez** üretilip atlas yüzeyinde saklanır. Her karede yeniden üretme.
- Sadece görünür tile'ları çiz (kamera alanı + 2 tile marj).
- Parçacık üst sınırı: ekranda aynı anda **max 200**.
- Toplu çizim için `Surface.blits()` kullan.
- Oyun kaydırmalı olduğu için **dirty rect tekniği işe yaramaz** — tam ekran çizim + yukarıdaki optimizasyonlar.
- Işıklandırma: tek karartma yüzeyi, `BLEND_RGBA_SUB` ile ışık delikleri. Yankı vinyeti **aynı yüzeyi** kullansın, ikinci geçiş açma.

---

## 5. KLASÖR YAPISI

```
lore/
├── CLAUDE.md
├── main.py
├── requirements.txt
├── docs/                  # tasarım belgeleri (salt okunur referans)
├── src/
│   ├── core/              # motor katmanı
│   │   ├── game.py        # ana döngü, sabit adım
│   │   ├── scene.py       # sahne yöneticisi
│   │   ├── camera.py      # takip, sarsıntı, look-ahead
│   │   ├── input.py       # girdi + tampon (buffer)
│   │   └── juice.py       # hitstop, sarsıntı, flaş
│   ├── entities/
│   │   ├── actor.py       # temel varlık
│   │   ├── player.py      # Rey / Ardo ortak
│   │   ├── enemy.py       # düşman temel sınıfı
│   │   └── enemies/       # tip başına dosya
│   ├── combat/
│   │   ├── hitbox.py
│   │   ├── combo.py       # zincir, pencere, iptal
│   │   └── damage.py
│   ├── systems/
│   │   ├── echo.py        # Yankı sistemi
│   │   ├── economy.py
│   │   ├── inventory.py
│   │   └── save.py
│   ├── world/
│   │   ├── tilemap.py
│   │   ├── level.py
│   │   └── rooms/         # bölüm verileri
│   ├── art/
│   │   ├── palette.py     # ★ 32 renk — TEK KAYNAK
│   │   ├── spritegen.py   # ★ prosedürel sprite üretimi
│   │   └── particles.py
│   ├── audio/
│   └── ui/
│       ├── text.py        # ★ tr_upper/tr_lower — Türkçe büyük/küçük harf
│       ├── menu.py        # ana menü, karakter seçimi, ayarlar
│       └── hud.py         # aşamalı açığa çıkarma, diegetik göstergeler
├── tools/                 # ★ asset boru hattı (oyundan ayrı, docs/asset-boru-hatti.md)
│   ├── palette.json       # 32 renk — TEK GERÇEK KAYNAK
│   ├── quantize.py        # her görsel buradan geçer
│   ├── outline.py         # otomatik kontur
│   ├── shade.py           # sol-üst ışık kuralı otomatik
│   ├── atlas.py           # spritesheet paketleme
│   ├── preview.py         # kontak sayfası — tutarsızlığı görmek için
│   ├── silhouette.py      # siluet testi otomasyonu
│   └── colorblind.py      # renk körü palet varyantları
├── assets/
│   ├── sprites/
│   ├── audio/
│   ├── fonts/
│   └── REGISTRY.md        # üretilen her asset'in kaydı
└── tests/
```

---

## 6. SANAT TUTARLILIK PROTOKOLÜ ★ (en kritik bölüm)

Bu projenin en büyük riski, farklı oturumlarda üretilen sprite'ların birbirini tutmaması.

### Palet
`src/art/palette.py` içinde **37 renk sabit** — kaynağı `tools/palette.json`. Her sprite bu paletten üretilir.
(32 idi; Arda 23.08.2026'da beş yeşil eklenmesini onayladı — palette hiç yeşil yoktu ve
`rot` zinciri Yankı'nın camgöbeğine bağlıydı. Gerekçe: `DEVIR.md` §7.)
**Palet dışı renk kullanmak yasaktır.** Yeni renk gerekiyorsa önce sor.
*Tek istisna:* Ardeko Studios intro logosu (dışarıdan gelen marka varlığı).

### Her görsel quantize'dan geçer
Kaynağı ne olursa olsun — kod, elle çizim, harici araç — her görsel `tools/quantize.py` filtresinden geçer. Bu tek kural tutarsızlık riskini yapısal olarak çözer. Detay: `docs/asset-boru-hatti.md`

**Blender veya 3D araç kullanılmaz.** 32×32 piksel sanat için yanlış araç. Boru hattı Pillow + NumPy üzerine kurulu.

### Sprite üretimi kod iledir
Sprite'ları PNG olarak elle çizme. `src/art/spritegen.py` içinde fonksiyon olarak üret:

```python
def draw_humanoid(surf, palette, pose, outfit, facing): ...
def draw_creature(surf, palette, body_type, pose): ...
```

Böylece Rey, Ardo ve muhafızlar **aynı iskeletten** çıkar. Tutarlılık garanti, varyasyon ucuz.

### Stil sözleşmesi — istisnasız
- **Işık kaynağı her zaman sol üstten**
- **Kontur:** siyah değil, paletin en koyu 2. rengi
- **Yüz:** ~~2 piksel göz, ağız yok~~ — **Arda 29.08.2026'da genişletti.**
  Oyun içi sprite'ta kafa ~7 piksel: göz + kaş + çene gölgesi (kaş eğimi
  karakteri ayırır). Gerçek yüz detayı — göz kapağı, iris, highlight,
  burun kümesi, dudak — **portrede** yaşıyor (`src/art/portrait.py`,
  64×96, kafa 40 piksel). Gerekçe ölçüldü: oyunun en dar geçidi 2 tile
  = 32px, sprite büyütülemez.
- **Sprite yüksekliği ≤ 32 piksel.** Bağlayıcı ve ölçülmüş
  (`tests/test_sprites.py`). Aşarsa karakter Bölüm 1/2'nin 2 tile'lık
  koridorlarından geçemez.
- **Kafa/boy oranı ≥ 4.4.** 3.5 chibi oranıdır; Arda açıkça yasakladı.
- **Gölge:** karakterin altında 1 elips
- **Animasyon hissi:** 8 FPS (her sanat karesi ≈ 7-8 oyun karesi)
- **Siluet testi:** her sprite tek renk siyaha çevrildiğinde ne olduğu anlaşılmalı

### Kayıt
Her yeni asset `assets/REGISTRY.md` dosyasına eklenir: ad, boyut, kare sayısı, üretildiği fonksiyon.

---

## 7. DÖVÜŞ — DEĞİŞTİRİLEMEZ DEĞERLER

`docs/dovus-sistemi.md` bağlayıcıdır. Kritik olanlar:

- Zincir penceresi: **12 kare** (Rey 14, Ardo 10)
- Hitstop: normal **3**, bitirici **7**, öldürücü **12** kare
- Kaçınma: **6 kare** dokunulmazlık, **18 kare** toplam
- Karşı vuruş penceresi: kaçınmadan sonra **9 kare**
- **Kill cancel:** düşman ölünce tüm recovery iptal
- **Saldırı hakkı:** aynı anda en fazla **2 düşman** saldırabilir
- **Tell süresi:** her düşman saldırısı en az **14 kare** önceden okunabilir

Bu değerleri kendi kafana göre değiştirme. Denge sorunu görüyorsan söyle, birlikte karar veririz.

### Game feel — bağlayıcı ek kurallar (`docs/derinlestirme.md` bölüm 1)

- **Üçlü senkron:** Hitstop, sarsıntı ve parçacık **tek bir `on_hit()` fonksiyonundan** tetiklenir. Ayrı çağrılırsa kare kayması olur, his bozulur.
- **Yönlü sarsıntı:** Sarsıntı rastgele değil, darbe vektörü yönünde. Bitirici aşağı iter, patlama radyal.
- **Rotasyon:** Orta/büyük sarsıntıya 0.3–0.8 derece rotasyon ekle. Saf öteleme hata gibi okunur, rotasyon kuvvet gibi okunur. Küçük sarsıntıda rotasyon yok.
- **Parçacık renk yolu:** Her parçacık ömrü boyunca palet üzerinde bir yol izler (parlak → koyu → is). Yollar `palette.py` içinde tanımlı.
- **Squash & stretch:** Yeni kare çizmeden `transform.scale` ile deformasyon. Zıplama 0.85/1.15, iniş 1.2/0.8, vuruş anında düşman 1.3/0.7.
- **Ses perde varyasyonu:** Her tekrarlı ses efekti ±%8 rastgele perdeyle çalınır. Tek satır, tekrar hissini yok eder.
- **Kalıcılık:** Kan lekeleri, moloz, kırık parçalar bölüm boyunca zeminde kalır.
- **Renk kodlu tehlike:** Palette bir "tehlike" rengi bulunur; her düşman tell'inde bu renkle parlar. Renk körlüğü için parlama **ve** siluet değişimi birlikte.
- **Düşman can barı yok.** Durum görsel olarak okunur (sendeleme, renk, hız). Sadece boss'larda bar var.

---

## 8. OYUNCU AFFI (sessiz yardımlar)

Bunlar oyuncuya asla söylenmez, ama her zaman aktiftir:
- **Coyote time:** platformdan düştükten sonra 6 kare zıplama hakkı
- **Girdi tamponu:** tuş 8 kare önceden basılırsa hafızada tutulur
- **Son şans:** can %15 altındayken öldürücü darbede 1 canla hayatta kal (bölüm başına 1)
- **Kaçınma cömertliği:** dokunulmazlık görsel başlangıçtan 2 kare önce başlar

---

## 9. UI / UX KURALLARI

Detay: `docs/menu-ui.md`. Bağlayıcı olanlar:

- **Hiçbir menü geçişi 12 kareyi (200ms) geçmez.** Menü hızlı hissetmeli.
- **Sinematik geçişler ani kesilmez.** Intro, dikey yolculuk ve ara sahnelerde tuşa basınca sert kesme YOK — basılı tutunca 3× hızlanır ve akıcı biçimde varır. (Menü içi geçişler bu kuralın dışında; onlar zaten kısa.)
- **Dikey/yatay kaydırmada ofset daima tam sayıya yuvarlanır.** Ondalık ofset piksel art dokusunu titretir.
- **DEVAM ET** her zaman en üstte ve önceden seçili. Kayıt yoksa **görünmez** (gri değil).
- **Yıkıcı eylemlerde varsayılan seçim daima İPTAL.** (Yeni oyun üzerine yazma, ana menüye dönme.)
- Ana menüye dönerken **kaydedildiğini açıkça yaz.** "Kaydedilmemiş ilerleme" belirsizliği asla oluşmasın.
- **Aşamalı açığa çıkarma:** can göstergesi hasar sonrası 3 sn, altın sayacı toplayınca, Yankı göstergesi kademe değişince görünür. Keşifte ekran temiz kalabilir.
- **Diegetik tercih et:** Yankı kademesi vinyet yoğunluğuyla, kolye pusulası boyundaki sprite parıltısıyla anlatılır — HUD çubuğuyla değil.
- **Üç girdi yöntemi de eşzamanlı çalışır:** klavye, gamepad, fare. Mod değiştirme gerekmez. Fare hareket edince imleç görünür, klavye kullanılınca kaybolur.
- **Kayıt güvenliği:** her zaman `save.json` + `save.bak.json`. Yazma sırasında çökme olursa yedekten dön.

### Türkçe metin — kritik
Gerekli karakterler: ğ Ğ ü Ü ş Ş ı I i İ ö Ö ç Ç

Python'un `str.upper()` fonksiyonu Türkçe için **yanlıştır**: `i` → `I` yapar, Türkçe'de `İ` olmalı; `ı` → `I` doğru ama `I` → `i` yanlış (`ı` olmalı). Menüde büyük harf kullanılacaksa `src/ui/text.py` içinde özel `tr_upper()` / `tr_lower()` fonksiyonları yaz ve her yerde onları kullan.

## 10. ERİŞİLEBİLİRLİK (baştan, sonradan değil)

Palet tek kaynak olduğu için bunların çoğu neredeyse bedava. Ayarlar menüsü yazıldığında hepsi bulunmalı:

- Ekran sarsıntısı kapatma
- Tam tuş yeniden atama (klavye + gamepad)
- Renk körü modu: 3 palet varyantı (protanopi, döteranopi, tritanopi)
- Tehlike göstergesi asla sadece renkle anlatılmaz — renk + şekil/siluet birlikte
- UI ölçekleme (2 kademe)
- Granüler zorluk: alınan hasar (%50/75/100/150), düşman hızı (%75/100), Yankı cezası açık/kapalı, otomatik combo açık/kapalı
- Dil: Türkçe + İngilizce. Diyalogsuz anlatım seçildiği için çeviri yükü sadece menülerde.

## 11. KOD STANDARTLARI

- **Türkçe:** yorumlar ve commit mesajları Türkçe. Değişken/fonksiyon adları İngilizce.
- **Tip ipuçları** zorunlu.
- **Sihirli sayı yok.** Tüm dövüş/denge değerleri `src/config.py` içinde adlandırılmış sabitler.
- **Dosya başına tek sorumluluk.** Bölmek iyi bir refleks ama
  **zorunlu değil** — 400 satır sınırını Arda kaldırdı (23.08.2026,
  bkz. `DEVIR.md` §3).
- **Global state yok.** Bağımlılıklar parametre olarak geçer.
- **Kısa fonksiyon.** 50 satırı geçen fonksiyon bölünür.

---

## 12. YASAKLAR

- ❌ Mobil/dokunmatik kod yazma
- ❌ `smoothscale` ile piksel art ölçekleme
- ❌ Palet dışı renk
- ❌ Değişken zaman adımı (`dt` tabanlı fizik)
- ❌ Sırası gelmemiş bölüm **içeriği** (odalar, düşman tipleri, boss'lar, ara sahneler) — altyapı serbest
- ❌ Yeni bağımlılık (sormadan)
- ❌ Placeholder yerine "geçici olarak basit sprite" üretip bırakmak — placeholder açıkça placeholder olsun
- ❌ Tasarım belgesindeki sayısal değerleri sessizce değiştirmek

---

## 13. ÇALIŞMA DÜZENİ

1. Görevi oku, `docs/` içinden ilgili belgeyi aç
2. **Plan modunda başla.** Büyük görevlerde önce keşfet ve yazılı bir plan sun — kod yazmadan. Onay alınca uygula. Bir özellik 20 karar noktası içerir; her birinde %80 isabet, hepsinde doğru olma ihtimalini %1'e düşürür. Plan bu kararları önceden netleştirir.
3. **Gürültülü araştırmayı alt-ajana ver.** Çok dosya okunması gerekiyorsa alt-ajanla yap, ana bağlamı temiz tut.
4. Kodu yaz
5. **Çalıştır ve kanıt göster.** "Çalışıyor" deme — test çıktısını, çalıştırdığın komutu ve döndürdüğünü göster. Kanıt yoksa başarı ilan etme.
6. Ne yaptığını özetle, açık kalan noktaları belirt
7. **Önerilerini listele** — gördüğün eksikler, iyileştirme fikirleri, riskler
8. Dur. Sıradaki göreve kendiliğinden geçme.

**Sandbox'ta çalışmayan bir adım varsa görevi "tamamlandı" ilan etme.** Neyin yapılamadığını açıkça söyle.

---

## 14. ÜRETİM SIRASI (mevcut durum)

- [x] Faz -1: İlk prototip (hareket, kılıç, düşman, HUD) — mevcut
- [ ] **Faz 0: Temel** — palet, font (Türkçe + tr_upper!), spritegen, klasör yapısı, sabit adım döngü
- [ ] **Faz 1: Dövüş çekirdeği** — zincir, hitstop, kill cancel, kaçınma (placeholder kutularla)
- [ ] **Faz 2: Düşman AI** — 3 tip + saldırı hakkı sistemi + ritim imzaları
- [ ] **Faz 3: Yankı sistemi** — 3 kademe, soru sorma, kolye pusulası, kırılabilir duvar
- [ ] **Faz 4: Bölüm 2** — 8 oda, mini-boss, gizli oda
- [ ] **★ ARA DEĞERLENDİRME** — kutularla eğlenceli mi? Değilse dur.
- [ ] **Faz 5: Menü ve UI** — işlevsel katman (menü, kayıt, ayarlar, HUD)
- [ ] **Faz 6: Menü sahnesi** — mor alev, rüzgâr, 5 aşamalı evrim
- [ ] **Faz 7: Bölüm 3** — meşale ekonomisi, ses haritası, Mum Bekçisi, Mor Alev
- [ ] **Faz 8: Sanat geçişi** — placeholder → gerçek sprite
- [ ] **Faz 9: Ses + son cila** — dikey katmanlama, erişilebilirlik

**Dikey dilim kriteri:** Bölüm 1-3 + menü bittiğinde oynayan biri "bir bölüm daha oynayayım" demiyorsa, devam etmeden önce dur ve tartış.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
