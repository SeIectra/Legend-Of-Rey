# AI ile görsel üretimi — promptlar ve yerleşim

Bu belge Arda'nın 31.08.2026'daki sorusunun cevabı: *"bana ihtiyacın
olan promptları yolla ve nereye hangi formatta koyacağımı söyle."*

---

## 0. Önce: her görselin izleyeceği yol

AI üreticileri **gerçek piksel sanatı üretmez** — yüksek çözünürlükte,
anti-aliasing'li, binlerce renkli "piksel görünümlü" bir görsel verir.
Doğrudan oyuna koyulamaz.

Aradaki üç adımı `tools/import_art.py` yapıyor: kırp → küçült →
37 renge çek.

```
python tools/import_art.py indirdigin.png --tur portre --ad rey
python tools/import_art.py indirdigin.png --tur panel  --ad chapter14_source_cevap
```

Araç ortalama renk kaymasını yazar. **26/255 altındaysa iyi**, üstünde
uyarır (kaynakta paletin karşılayamadığı ton var demektir).

Ölçtüm: referans olarak gönderdiğin Rey portresi bu yoldan geçince
kayma **7.2/255** çıktı — palet AI çıktısını rahat karşılıyor.

---

## 1. Palet — prompta yapıştır

Üretici paleti tam tutturmaz ama yaklaştırırsa quantize sonrası daha
temiz olur. 37 renk:

```
#06050B #100E1A #1E1B2C #282C3C #3A4054 #565E74 #7E869E
#0E1A30 #183256 #285888
#3A261C #68462C
#5C2014 #B0461C #EC8230 #FFC660
#3E0E14 #8A1A22 #D43836
#623C2C #9A664A #CA9876
#163E4A #368E9A #82DEE4
#2E144A #6A34A0 #B47EEA
#D84C22 #FF863C
#E4DECC #FCFAF6
#12221C #223E2A #406C3A #6E9E52 #B0C86E
```

**Her promptun sonuna eklenecek ortak kuyruk:**

```
Pixel art, limited palette, hard-edged pixel clusters, NO anti-aliasing,
NO blur, NO gradients, NO text, NO watermark, NO signature.
Light source strictly from the UPPER LEFT.
Dark fantasy dungeon, muted and desaturated, cold stone and torchlight.
Palette limited to: #06050B #100E1A #1E1B2C #282C3C #3A4054 #565E74
#7E869E #0E1A30 #183256 #285888 #3A261C #68462C #5C2014 #B0461C
#EC8230 #FFC660 #3E0E14 #8A1A22 #D43836 #623C2C #9A664A #CA9876
#163E4A #368E9A #82DEE4 #2E144A #6A34A0 #B47EEA #D84C22 #FF863C
#E4DECC #FCFAF6 #12221C #223E2A #406C3A #6E9E52 #B0C86E
```

---

## 2. ÖNCELİK 1 — Portreler (3 dosya) ★★★

**En yüksek getiri.** Yüz, diyalog kutusunda, karakter seçiminde,
prologda ve **14 sinematik yakın çekiminde** görünüyor. Yani üç dosya
çizersen oyunun her duygusal anı birden yükseliyor.

| Nereye | `assets/portraits/rey.png` · `ardo.png` · `cemo.png` |
|---|---|
| **Boyut** | 64 × 96 (araç küçültüyor — sen 512×768 üret) |
| **Kadraj** | Baş ve omuzlar. Kafa üstte, tepede 4-5 piksel boşluk |
| **Arka plan** | **Düz tek renk** (`#100E1A`) — kesmesi kolay olsun |

### REY

```
Head-and-shoulders portrait of a young woman, late teens, pixel art.
Wavy dark brown hair falling past the shoulders, loose strands framing
the face, visible hair volume and direction — not a flat block.
Warm tan skin. Large expressive dark eyes with THREE tones: sclera,
iris, pupil, plus one small highlight in the upper left of each iris.
Clear facial bone structure: cheekbones catching light, a defined nose
bridge with a distinct tip, a soft jawline. Upper and lower lip
readable as separate shapes. Calm, tired, determined expression —
someone who has not slept.
Wearing a deep blue hooded tunic (#183256) with a small red mark on
the chest. Fabric shows two tones, not one flat colour.
Centered, facing slightly to the left, plain dark background #100E1A.
[ORTAK KUYRUK]
```

### ARDO

```
Head-and-shoulders portrait of a young man, early twenties, pixel art.
Short messy dark hair, a few strands falling over the forehead.
Warm brown skin. Sharp, mature, confident expression — a tracker who
reads the ground. Heavy brows, deep-set eyes with THREE tones and a
small highlight. Strong jawline and cheekbones with HIGH light-shadow
contrast — more contrast than a soft face would have. Faint stubble
along the jaw, subtle, not a beard.
Wearing dark grey-blue cloth (#3A4054) with a rounded steel pauldron
on each shoulder (#565E74) — cloth and metal must read as DIFFERENT
materials, metal harder and brighter.
Centered, facing slightly to the left, plain dark background #100E1A.
[ORTAK KUYRUK]
```

### CEMO

```
Head-and-shoulders portrait of a young boy, about ten years old,
pixel art. CHILD proportions: larger head relative to shoulders,
rounder cheeks, softer jaw — must not look like a small adult.
Curly dark brown hair. Warm tan skin, same family as Rey — they are
siblings and it should show in the eyes and nose.
Big frightened but stubborn eyes with three tones and a highlight.
Wearing a simple brown tunic (#68462C), plain, worn.
Centered, facing slightly to the left, plain dark background #100E1A.
[ORTAK KUYRUK]
```

Bitince:

```
python tools/import_art.py rey_ai.png --tur portre --ad rey
python tools/import_art.py ardo_ai.png --tur portre --ad ardo
python tools/import_art.py cemo_ai.png --tur portre --ad cemo
```

Beğenmezsen dosyayı sil — oyun prosedürel portreye geri döner.

---

## 3. ÖNCELİK 2 — Sinematik panelleri

Toplam **91 arka plan paneli** var (14 tanesi yakın çekim; onlar
portre kullanıyor, panel istemiyor). Hepsini üretmek gerçekçi değil.

| Nereye | `assets/panels/<dosya>.png` |
|---|---|
| **Boyut** | 480 × 270 (16:9 — sen 1920×1080 üret) |
| **Ad** | `<bolum>_<sahne>_<panel>.png` — tam liste aşağıda |

Dosya adı yanlışsa **sessizce yok sayılır** ve prosedürel arka plan
çizilir. Adları `python tools/panel_list.py` ile dökebilirsin.

### En çok kazandıran 8 panel

Bunlar oyunun dönüm noktaları. Sekiz dosya, sekiz an:

| Dosya | Ne |
|---|---|
| `chapter14_source_cevap.png` | ★ Twist anı — sesin dışarıdan geldiği kare |
| `chapter13_cage_gorus.png` | ★ Cemo kafeste, Rey'e bakıyor |
| `chapter06_ardo_entrance_bakisma.png` | Ardo'nun girişi, ilk bakışma |
| `chapter03_purple_beliris.png` | Mor Alev'in belirişi |
| `chapter07_hand_temas.png` | İlk temas — el ele |
| `chapter08_fireside_sarma.png` | Ateş başı, yara sarma |
| `chapter10_parting_gidis.png` | Ayrılık |
| `chapter12_camp_duzenek.png` | Ardo'nun kurduğu düzenek |

**Örnek prompt — `chapter14_source_cevap.png`:**

```
Wide cinematic scene, 16:9, pixel art. Deep underground dungeon
chamber of dark carved stone. In the FOREGROUND LEFT, small, the
silhouette of a lone figure with a sword, seen from behind, dwarfed
by the space. In the BACKGROUND RIGHT, a vast bottomless opening in
the rock, and out of it a violet glow (#6A34A0, #B47EEA) pouring
toward the figure — the light comes FROM the pit, not from the
figure. The violet must clearly be the strongest light in the frame.
Oppressive, vertical, the chamber taller than it is wide.
No characters' faces visible. Atmospheric dust in the air.
[ORTAK KUYRUK]
```

**Örnek prompt — `chapter13_cage_gorus.png`:**

```
Wide cinematic scene, 16:9, pixel art. A prison block of dark stone
with iron bars. On a RAISED LEDGE in the upper right, an iron cage
lit by a single warm lantern (#EC8230). Below and to the left, on the
floor of the chamber, a small lone figure looking UP at the cage —
the vertical distance between them is the subject of the image.
Everything else in cold shadow (#1E1B2C, #282C3C); the cage is the
only warm thing in the frame.
No readable faces. Bars, chains, wet stone.
[ORTAK KUYRUK]
```

Kalan panellerde de aynı kalıp işe yarıyor:
**mekân + kamera + ışığın nereden geldiği + tek bir duygu.**
Yüz detayı isteme — 480×270'te yüz zaten okunmuyor, o iş portrenin.

---

## 4. ÜRETME — bunlar koddan geliyor

Zaman kaybetme, bunları AI'ya çizdirme:

- **Karakter/düşman sprite'ları** — `src/art/spritegen.py` üretiyor.
  `CLAUDE.md` §6 elle PNG çizmeyi açıkça yasaklıyor; tutarlılık
  garantisi buna dayanıyor.
- **Tile setleri, parçacıklar, ışık maskeleri** — hepsi kod.
- **UI, font, menü** — kod.

---

## 5. Özet

| Öncelik | Adet | Nereye | Etki |
|---|---|---|---|
| 1 | **3 portre** | `assets/portraits/` | Her diyalog + 14 yakın çekim |
| 2 | **8 panel** | `assets/panels/` | Oyunun 8 dönüm noktası |
| 3 | 83 panel daha | `assets/panels/` | Kalan sinematikler |

Üçünü de tek tek ekleyebilirsin — dosya yoksa oyun çalışmaya devam
ediyor, dosya varsa daha iyi görünüyor. Hepsini birden bitirmek
gerekmiyor.
