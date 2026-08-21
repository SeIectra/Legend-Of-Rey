# LORE — ASSET ÜRETİM BORU HATTI
**GDD Ek H** · Hangi araç neye yarar

---

## KISA CEVAP

**Blender gerekmez.** 32×32 piksel sanat için yanlış araç ve gereksiz karmaşıklık ekliyor.

İşe yarayan üçlü:

| Araç | Ne için | Neden |
|---|---|---|
| **Pillow + NumPy** | Sprite üretimi, palet işleme, atlas paketleme | Zaten Python, Claude Code doğrudan kullanır, sıfır kurulum sürtünmesi |
| **Aseprite CLI** | Toplu dönüşüm, spritesheet paketleme, palet uygulama | Piksel sanatın standart aracı, script API'si var (opsiyonel — ücretli) |
| **Pygame'in kendisi** | Efektler, ışık, parçacıklar, aura | Zaten oyunda; sprite yerine kod olarak üretilir |

**Ana strateji değişmiyor:** Sprite'lar PNG dosyası olarak değil, `spritegen.py` içinde **fonksiyon** olarak üretiliyor. Boru hattı bunu destekliyor, değiştirmiyor.

---

## 1. NEDEN BLENDER DEĞİL

- 32×32'de her piksel elle konumlandırılmış bir karardır. 3D render küçültülünce bulanık ve okunaksız olur — Rey'in yüzü 2 piksel göz, bunu render'dan elde edemezsin
- Kurulum, sahne yönetimi, render ayarları, quantize boru hattı — hepsi bakım maliyeti
- Kazanç sadece boss'lar ve panellerde olurdu, o da marjinal
- Prototip zaten prosedürel yöntemle iyi sonuç veriyor. Çalışan şeyi değiştirme

**İstisna:** Eğer ileride Blender zaten biliyorsan ve büyük bir boss için özel bir şey gerekiyorsa, tek seferlik kullanılabilir. Ama boru hattına dahil etme.

---

## 2. PILLOW + NUMPY BORU HATTI ★ (asıl sistem)

`tools/` klasörü altında, oyundan **ayrı** çalışan yardımcı script'ler.

```
tools/
├── palette.json          # 32 renk — src/art/palette.py ile aynı kaynak
├── quantize.py           # herhangi bir görseli palete indirger
├── outline.py            # sprite'a otomatik kontur ekler
├── shade.py              # sol-üst ışık kuralına göre gölgeleme
├── atlas.py              # sprite'ları tek atlas PNG'ye paketler
├── preview.py            # tüm asset'leri tek bir kontak sayfasında gösterir
├── silhouette.py         # siluet testi — hepsini siyaha çevirip yan yana dizer
└── colorblind.py         # 3 renk körü palet varyantını üretir
```

### 2.1 quantize.py
Herhangi bir görseli (elle çizilmiş, AI üretimi, fotoğraf) **32 renkli palete** indirger.

- Her pikseli palet renklerine olan öklid mesafesine göre en yakına yuvarlar
- Dithering **kapalı** (piksel artta dithering genelde kirletir)
- Alfa kanalı korunur, yarı saydam pikseller eşiğe göre 0 veya 255'e yuvarlanır

**Kullanım:** Dışarıdan gelen her görsel bu filtreden geçer. Böylece kaynağı ne olursa olsun tutarlılık garanti.

### 2.2 outline.py
Sprite'ın dış kenarına otomatik kontur ekler. Kontur rengi paletin **en koyu 2. rengi** (siyah değil — CLAUDE.md kuralı).

- Alfa maskesini dilate et, orijinali çıkar, kalan halka = kontur
- İç kontur opsiyonel (kol/bacak ayrımı için)

### 2.3 shade.py
Sol-üst ışık kuralını otomatik uygular.

- Sprite'ın alfa maskesinden bir normal haritası tahmin et (mesafe dönüşümü)
- Sol-üst yönde parlaklık +1 palet kademesi, sağ-alt −1 kademe
- Sonuç paletten çıkmaz

**Bu, ışık tutarlılığı sorununu kökten çözer.** Elle çizerken unutulan kural, burada otomatik.

### 2.4 atlas.py
Üretilen tüm sprite'ları tek bir PNG'ye paketler + bir JSON indeks üretir.

- Yükleme süresi düşer (100 dosya yerine 1)
- `assets/REGISTRY.md` otomatik güncellenir

### 2.5 preview.py ★ en kullanışlısı
Tüm asset'leri tek bir "kontak sayfası" PNG'sinde yan yana dizer, altlarında isimleri.

**Neden kritik:** Tutarsızlığı ancak yan yana görünce fark edersin. Bu sayfayı her üretim turundan sonra açıp bak — biri farklı duruyorsa hemen görürsün.

### 2.6 silhouette.py
Bütün sprite'ları tek renk siyaha çevirip dizer. **Siluet testi** otomatikleşir: ne olduğu anlaşılmayan sprite yeniden çizilir.

### 2.7 colorblind.py
Ana paletten protanopi / döteranopi / tritanopi varyantlarını üretir. Erişilebilirlik neredeyse bedava hale gelir.

---

## 3. ASEPRITE CLI (opsiyonel, faydalı)

Piksel sanatın standart aracı. Ücretli (~20 USD) ama tek seferlik.

**Komut satırından kullanılabilir** — yani Claude Code otomatikleştirebilir:

```bash
aseprite -b sprite.aseprite --sheet atlas.png --data atlas.json
aseprite -b input.png --palette lore.gpl --save-as output.png
aseprite -b anim.aseprite --scale 3 --save-as preview.gif
```

**Ne zaman değer:** Elle rötuş yapmak istediğinde. Prosedürel üretim %85'i halleder, kalan %15 (Rey'in yüz ifadesi, boss'un imza pozu) elle dokunuş ister. Aseprite bu dokunuşu yapıp sonucu boru hattına geri vermenin en temiz yolu.

**Ne zaman gereksiz:** Her şey koddan üretiliyorsa. Başlangıçta atla, ihtiyaç doğunca al.

---

## 4. PYGAME İLE KOD-ASSET (zaten planda)

Sprite olması gerekmeyen her şey kod olarak üretilir:

| Öğe | Yöntem |
|---|---|
| Slash yayı, impact, kan, toz | Parçacık sistemi |
| Mor alev aurası | Radyal gradyan + additive blend |
| Işık/karanlık maskesi | Tek yüzey + `BLEND_RGBA_SUB` |
| Rüzgâr (pelerin, saç, su) | Dikey dilim kaydırma (shear) |
| Mum Bekçisi'nin gözleri | İki parçacık emitörü |
| UI panelleri, çerçeveler | `pygame.draw` + 9-slice |
| Menü zincirleri, toz | Sinüs hareketi + parçacık |
| Yükleme/geçiş bulanıklığı | 4× küçült → 4× büyüt |

**Bu liste asset listesinden ~150 parça düşürüyor.**

---

## 5. AI GÖRSEL ÜRETİMİ — dikkatli kullan

Harici AI görsel araçları (Claude Code değil — ayrı servisler) ara sahne panelleri için düşünülebilir.

**Sorun:** Piksel artta tutarlılık kötü. Aynı karakteri iki kez aynı üretemezsin. 40 panelde Rey 40 farklı kişi olur.

**Çalışan yöntem:** AI'yı **kompozisyon taslağı** için kullan, final için değil.
1. AI'dan sahne kompozisyonu üret (kaba, büyük çözünürlük)
2. `quantize.py`'den geçir
3. Üzerine oyun sprite'larını yerleştir (karakterler mutlaka gerçek sprite olsun)
4. Arka plan AI'dan, karakterler oyundan → tutarlılık korunur

**Ya da hiç kullanma.** Menü belgesindeki panel stratejisi (sahnelenmiş oyun görüntüsü + siluet + 6 gerçek illüstrasyon) zaten yeterli.

---

## 6. ÖNERİLEN KURULUM SIRASI

1. `tools/palette.json` — tek gerçek kaynak, `src/art/palette.py` bunu okur
2. `quantize.py` — her şey buradan geçecek
3. `outline.py` + `shade.py` — stil sözleşmesi otomatikleşir
4. `preview.py` — ilk sprite'lardan itibaren kullan
5. `silhouette.py` — her üretim turunda çalıştır
6. `atlas.py` — sprite sayısı 50'yi geçince
7. `colorblind.py` — erişilebilirlik fazında
8. Aseprite — elle rötuş ihtiyacı doğunca

---

## 7. ALTIN KURAL

**Palet tek kaynaktır.** `tools/palette.json` değişirse her şey değişir. Bu dosyayı erken sabitle ve bir daha dokunma.

Kaynağı ne olursa olsun — kod, elle çizim, Aseprite, AI — her görsel `quantize.py`'den geçer. Bu tek kural, projenin en büyük riskini (tutarsızlık) yapısal olarak çözer.
