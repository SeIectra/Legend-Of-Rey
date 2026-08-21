# LORE — Asset Listesi
**GDD Ek C** · v0.1

**Teknik standart:** 480×270 iç çözünürlük · 32×32 karakter · 16×16 tile · 60 FPS
**Format:** PNG spritesheet (yatay şerit), OGG ses
**Palet:** Tek ana palet — 32 renk. Tüm asset'ler bu paletten. Tutarlılık kaliteyi bedava artırır.

---

## A. KARAKTER ANİMASYONLARI

### Rey (32×32) — ~62 kare

| Animasyon | Kare | Not |
|---|---|---|
| Boşta (idle) | 4 | Nefes alıp verme, saç hareketi |
| Yürüme | 6 | |
| Koşma | 8 | |
| Zıplama (yükseliş) | 2 | |
| Havada asılı | 2 | |
| Düşüş | 2 | |
| İniş | 3 | Toz efektiyle senkron |
| Saldırı 1 | 4 | 4 ön + 3 aktif + 8 son karesine yayılır |
| Saldırı 2 | 4 | |
| Saldırı 3 (bitirici) | 6 | Daha büyük, daha geniş |
| Havaya kaldırma | 4 | Yukarı doğru yay |
| Havada saldırı | 3 | |
| Kaçınma | 5 | Yarı saydam iz bırakır |
| Hasar alma | 2 | |
| Ölüm | 6 | |
| Yankı aktif (boşta) | 4 | Gözler parlar, hafif titrer |
| Merdiven/tırmanma | 4 | |
| Etkileşim (kol çevirme) | 3 | |

### Ardo (32×32) — ~55 kare
Aynı liste, Yankı animasyonları hariç. Daha ağır, daha az kare (yavaşlık hissi). Farklı silah silueti.

### Cemo (24×24) — ~14 kare
Sadece ara sahneler: boşta, koşma, kafeste, uzanma. Az iş, yüksek duygusal getiri.

---

## B. DÜŞMANLAR

Her düşman için standart set: **boşta, yürüme, saldırı (tell dahil), hasar, ölüm** ≈ 20–28 kare

### Katman 1 — Çürüyenler (32×32)
1. **Sürüklenen** — 20 kare
2. **Tırmanan** — 26 kare (duvar/tavan varyantı ekstra)
3. **Şişkin** — 24 kare (patlama animasyonu dahil)

### Katman 2 — Lanetli Muhafızlar (32×40, biraz uzun)
4. **Kalkanlı** — 26 kare (kalkan kırılma dahil)
5. **Mızraklı** — 24 kare
6. **Okçu** — 22 kare + ok mermisi
7. **Komutan** — 28 kare (çağırma animasyonu)

### Katman 3 — Yankı'nın Çocukları (değişken)
8. **Sessiz** — 22 kare (yarı saydam render)
9. **Yankılayan** — 26 kare (oyuncu silueti taklidi)
10. **Bölünen** — 24 kare + küçük varyant

**Toplam düşman:** ~240 kare

---

## C. BOSS'LAR (64×64 veya 96×96)

Her boss: boşta, 3–4 saldırı, faz geçişi, hasar, ölüm ≈ **45–60 kare**

| Boss | Bölüm | Boyut |
|---|---|---|
| 1 — Çürümüş Muhafız | B6 | 64×64 |
| 2 — Zindancı | B13 | 64×80 |
| 3 — Yankı Kaynağı | B14 | 96×96 |
| 4 — Final | B18 | 96×96 |

**Toplam:** ~210 kare

---

## D. TILESET (16×16)

Her katman için tam set:

| Parça | Adet |
|---|---|
| Zemin (köşe/kenar/orta varyantları) | ~20 |
| Duvar | ~16 |
| Tavan / sarkıt | ~8 |
| Platform | ~6 |
| Merdiven | 3 |
| Arka plan katmanı (parallax) | ~12 |
| Dekor (moloz, kök, zincir) | ~15 |

**Katman başına ~80 tile × 3 katman = ~240 tile**

### Hikâye Dekorları (environmental storytelling)
Ucuz ama anlatımın belkemiği:
- Tırmık izleri (Cemo'nun boyunda) — 3 varyant
- İskelet / önceki maceracı — 4 varyant
- Sönmüş meşale, yarım kamp — 3
- Duvara kazınmış işaretler — 5
- Ardo'nun bıraktığı işaretler — 4
- Kan/leke izleri — 4

**~23 dekor sprite'ı.** Neredeyse bedava, anlatımın yarısı bunlarda.

---

## E. EFEKTLER

| Efekt | Kare |
|---|---|
| Vuruş slash (silah tipine göre 3 varyant) | 3×4 |
| Vuruş çarpma (impact) | 5 |
| Kan / öz sıçraması | 6 |
| Ölüm dağılması | 6 |
| Toz (iniş, koşu) | 4 |
| Kaçınma izi | 4 |
| Patlama (Şişkin) | 8 |
| Yankı dalgası (rezonans) | 6 |
| Sandık açılma | 5 |
| Altın parıltısı | 4 |
| Kıvılcım / meşale ateşi | 6 |
| Su sıçraması | 5 |
| Işık huzmesi (ayna bölümü) | statik + 3 |

**Toplam:** ~75 kare

---

## F. ARAYÜZ (UI)

| Öğe | Adet |
|---|---|
| Can barı çerçevesi + dolgu | 3 |
| Yankı göstergesi (3 kademe) | 3 |
| Combo sayacı rakamları | font |
| Altın ikonu | 1 |
| Ekipman ikonu (silah 8, zırh 6, tılsım 10) | 24 |
| Yetenek ağacı ikonu | 12 |
| Buton / çerçeve / panel | ~10 |
| Konuşma balonu + ikon seti (kalp, soru, kafatası, kılıç, anahtar, ünlem) | 8 |
| Menü arka planı | 3 |

**Toplam:** ~65 parça

**Font:** Tek bir piksel font yeterli (ücretsiz seçenekler bol). Türkçe karakter desteği şart — ğ, ü, ş, ı, ö, ç.

---

## G. ARA SAHNE PANELLERİ

En pahalı görsel kalem. **~40 statik panel** (480×270, tam ekran illüstrasyon).

| Bölüm | Panel |
|---|---|
| B1 Köy | 5 (kolye, gece, yarık, Cemo'nun düşüşü, Rey'in eli) |
| B6 Ardo girişi | 4 |
| B7 El tutma | 2 |
| B8 Ateş başı | 4 |
| B10 Ayrılık | 2 |
| B12 Mektup | 3 |
| B13 Cemo | 3 |
| B14 Twist | 4 |
| B16 Sırt sırta | 3 |
| B17 Camdan bakış | 2 |
| B18 Final + son | 6 |
| Karakter seçim ekranı | 2 |

**Not:** Bunlar tam illüstrasyon olmak zorunda değil. Oyun içi sprite'ları büyük ölçekte, özel pozlarla kullanmak hem ucuz hem tutarlı görünür. Dan the Man tam olarak bunu yapıyor.

---

## H. SES

### Ses Efektleri (~65)
| Kategori | Adet |
|---|---|
| Vuruş (silah tipi × temas tipi) | 12 |
| Düşman sesi (tip başına 2–3) | 25 |
| Ayak sesi (taş/su/çakıl × 4 kare) | 12 |
| UI (buton, satın alma, hata) | 6 |
| Sandık, kapı, kol, vana | 8 |
| Yankı fısıltıları | 10 |
| Ortam döngüleri (damla, rüzgâr, uğultu) | 6 |

### Müzik (8–10 parça)
- Ana menü
- Katman 1 ortam
- Katman 2 ortam
- Katman 3 ortam
- Dövüş yoğunluk katmanı (ortama üstüne binen)
- Nefes/ateş başı teması (romantik yayın müziği)
- Boss teması
- Final teması
- Zafer / son

**Yankı ses işlemi:** Her ses efektinin bir de "filtrelenmiş" versiyonu gerekir (boğuk). Pygame'de gerçek zamanlı filtre yok — önceden işlenmiş ikinci set hazırla. Kritik seslerde yeterli (~20 dosya).

---

## İ. TOPLAM

| Kategori | Miktar |
|---|---|
| Karakter kareleri | ~131 |
| Düşman kareleri | ~240 |
| Boss kareleri | ~210 |
| Tile | ~240 |
| Hikâye dekoru | ~23 |
| Efekt kareleri | ~75 |
| UI parçası | ~65 |
| Ara sahne paneli | ~40 |
| Ses efekti | ~65 |
| Müzik | ~9 |

---

## J. DİKEY DİLİM İÇİN GEREKEN MİNİMUM

Bölüm 2'yi tam cilalı bitirmek için sadece bunlar lazım — **listenin %15'i**:

**Görsel**
- Rey tam animasyon seti (~62 kare)
- Sürüklenen, Tırmanan, Şişkin (~70 kare)
- Mini-boss (büyütülmüş Sürüklenen + 1 saldırı, ~12 kare)
- Katman 1 tileset (~80 tile)
- Hikâye dekoru: tırmık izi, iskelet, meşale (~10)
- Efektler: slash, impact, kan, toz, ölüm, sandık (~30 kare)
- UI: can barı, Yankı göstergesi, combo, altın, 3 ekipman ikonu (~12)

**Ses**
- Vuruş 4, düşman 8, ayak 6, UI 3, sandık 2, Yankı fısıltı 3 (~26)
- Müzik: Katman 1 ortam + dövüş katmanı (2 parça)

**Toplam: ~280 görsel parça + ~28 ses.** Bir kişi için gerçekçi bir hedef.

---

## K. ÜRETİM STRATEJİSİ ÖNERİSİ

1. **Palet önce.** 32 renk sabitle, her şey ondan çıksın. Sonradan palet değiştirmek tüm asset'i çöpe atar.
2. **Placeholder ile başla.** Renkli dikdörtgenlerle oyna, oynanış oturunca sanat yap. Güzel sprite'la kötü oynanışı fark edemezsin.
3. **Rey'i en son cilala.** En çok bakılan sprite o; oynanış netleşmeden animasyon yaparsan iki kez yaparsın.
4. **Tileset'i modüler kur.** 9-slice mantığı (köşe/kenar/orta) — 20 tile ile sonsuz oda.
5. **Ses için ücretsiz kütüphaneler.** freesound.org, sfxr/Bfxr (piksel oyun sesi üretici), OpenGameArt. Müzik en son.
6. **Ara sahne panellerini oyun sprite'ından üret.** Ayrı illüstrasyon çizme — büyütülmüş sprite + özel poz yeter.
