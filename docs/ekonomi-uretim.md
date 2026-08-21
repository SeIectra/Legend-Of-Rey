# LORE — Ekonomi, Zorluk Eğrisi & Üretim Planı
**GDD Ek B** · v0.1

---

## 1. EKONOMİ FELSEFESİ

Tek para birimi: **Altın**. İkinci bir kaynak yok — karmaşıklık kaliteyi artırmıyor, sadece menü sayısını artırıyor.

**Temel kural:** Oyuncu her bölümde bir şey satın alabilmeli, ama her şeyi alamamalı. Seçim yapmak zorunda kalmalı.

### Altın Kaynakları

| Kaynak | Miktar |
|---|---|
| Normal düşman | 3–8 |
| Mini-boss | 40–60 |
| Boss | 150–250 |
| Sandık (ana yol) | 25–40 |
| Sandık (gizli) | 60–100 |
| Combo çarpanı | ×1.2 / ×1.5 / ×2 |
| Bulmaca ödülü | 50–80 |

**Bölüm başına beklenen gelir:** ~180 (dikkatsiz oyun) → ~350 (her şeyi bulan oyun)

Aradaki fark bilerek büyük. Keşif ödüllendirilmeli — temel duygun "keşif + güçlenme".

### Harcama Kalemleri

| Kalem | Fiyat aralığı | Not |
|---|---|---|
| Silah | 200–900 | Bölüm katmanına göre |
| Zırh | 180–800 | |
| Tılsım | 300–1200 | En pahalı — en çok oynanış değiştiren |
| Can şişesi (tek kullanım) | 40 | Bölüm başına 3 taşıma limiti |
| Yetenek puanı | 150, 250, 400, 600... | Artan maliyet |
| Yankı onarımı (acil) | 120 | Nefes bölümü beklemeden kademe geri al |

### Denge Kontrolü

18 bölüm × ~250 ortalama = **~4500 altın** toplam gelir.
Ölüm kayıpları ve sarf malzemeleri ≈ %20 → **~3600 harcanabilir**.

Bu, oyuncunun oyun boyunca kabaca **4 silah, 3 zırh, 2 tılsım ve 6 yetenek puanı** almasına yeter. Yani mevcut ekipmanın belki yarısını satın alabilir — geri kalanı için seçim yapmalı, ikinci oynayışta farklı bir yol deneyebilir.

**Kritik:** Ekipman satılamaz. Satış varsa oyuncu her şeyi alır, seçim ölür.

---

## 2. ZORLUK EĞRİSİ

Düz artan bir çizgi değil — **testere dişi**. Her katman başında zorluk düşer (yeni mekanik öğreniliyor), sonra tırmanır, boss'ta zirve yapar, sonra tekrar düşer.

| Bölüm | Zorluk (1-10) | Neden |
|---|---|---|
| B1 | 1 | Tutorial |
| B2 | 2 | Combo öğrenimi |
| B3 | 3 | Meşale kısıtı |
| B4 | — | Nefes, dövüş yok |
| B5 | 3 | Bulmaca ağırlıklı |
| B6 | **5** | Boss 1, ama Ardo yanında |
| B7 | 3 | Yeni katman, öğretim |
| B8 | — | Nefes |
| B9 | 4 | Dikey + rezonans |
| B10 | **6** | Yalnızlık + Yankı ihaneti |
| B11 | 5 | Bulmaca ağırlıklı |
| B12 | — | Nefes |
| B13 | **7** | Boss 2, kovalamaca |
| B14 | **7** | Boss 3, twist |
| B15 | 4 | Gizlilik — farklı beceri |
| B16 | 6 | Team-up, kalabalık |
| B17 | 5 | Bulmaca ağırlıklı |
| B18 | **9** | Final, yardımsız |

**Nefes bölümleri zorluk eğrisinin parçasıdır.** Sürekli tırmanan gerilim yorar; düşüşler zirveleri yükseltir.

### Düşman Yoğunluğu

| Katman | Aynı anda ekranda | Bölüm başına toplam |
|---|---|---|
| 1 (B1-6) | 3–5 | 25–35 |
| 2 (B7-13) | 4–7 | 35–50 |
| 3 (B14-18) | 5–8 | 40–60 |

Saldırı hakkı sistemi (aynı anda 2 saldıran) sayesinde 8 düşman bile okunabilir kalır.

### Bölüm Süresi Hedefi

- Normal bölüm: **8–12 dakika**
- Nefes bölümü: **3–5 dakika**
- Boss bölümü: **12–18 dakika**

Toplam ilk oynayış: **~4 saat**. Her şeyi bulan oyuncu: **~6 saat**. İki karakter × 2 = tekrar oynanabilirlik.

Bu, Pygame'de küçük ekiple gerçekçi bir hedef. 10 saatlik oyun vaadi projeyi öldürür.

---

## 3. ÜRETİM PLANI

### Aşama 0 — Teknik Temel (1. iş)
Karakter kontrolü, çarpışma, kamera, tile haritası yükleme, sahne yöneticisi.
**Çıktı:** Boş bir odada koşup zıplayan karakter.

### Aşama 1 — DİKEY DİLİM ★ (en kritik)
**Sadece Bölüm 2.** Ama tam cilalı: dövüş, hitstop, 3 düşman tipi, mini-boss, bir gizli sandık, ses, ara sahne paneli, ekipman ekranı.

**Neden B2:** B1 tutorial olduğu için atipik. B2 oyunun *normal* dokusunu temsil ediyor — dövüş, keşif, gizli alan. Kalite çıtası burada belirlenir.

**Bitiş kriteri:** Bu bölümü oynayan biri "bu oyunu satın alırım" diyorsa geçtik. Demiyorsa 17 bölüm daha yapmanın anlamı yok.

### Aşama 2 — Katman 1 (B1–B6)
Dikey dilimi şablon alarak çoğalt. Boss 1 burada. Ardo'nun girişi ve team-up AI'sı ilk kez burada.

### Aşama 3 — Katman 2 (B7–B13)
Yeni düşman ailesi, yeni bulmaca mekanikleri. Boss 2.

### Aşama 4 — Katman 3 (B14–B18)
Twist, Yankı'nın tersine dönmesi, Boss 3 ve 4. Final.

### Aşama 5 — İkinci Karakter
Ardo oynanışı. Kod büyük ölçüde hazır — istatistik farkları, Yankı'sız UI, değişen ara sahneler.

### Aşama 6 — Cila
Ses geçişleri, menüler, ayarlar, denge testleri, hata avı.

---

## 4. ASSET BÜTÇESİ (gerçekçi tahmin)

| Kalem | Adet |
|---|---|
| Oynanabilir karakter | 2 × ~60 kare |
| Düşman tipi | 10 × ~25 kare |
| Boss | 4 × ~50 kare |
| Tileset | 3 katman × ~80 tile |
| Ara sahne paneli | ~40 statik görsel |
| Ekipman ikonu | ~35 |
| Efekt (slash, patlama, toz) | ~15 set |
| Ses efekti | ~60 |
| Müzik parçası | 8–10 |

**Bu, projenin gerçek maliyeti.** Kod AI ile hızlanır, bu liste hızlanmaz. Erken başla.

---

## 5. TEKNİK KARARLAR

| Karar | Değer | Gerekçe |
|---|---|---|
| Çözünürlük | 480×270 iç, tam ekrana ölçekli | 16:9, tam sayı katları (2×, 3×, 4×) |
| Karakter boyutu | 32×32 | Detay/iş dengesi |
| Tile boyutu | 16×16 | Standart, level tasarımı esnek |
| Kare hızı | Sabit 60 | Dövüş kare hassasiyeti gerektiriyor |
| Fizik | Sabit adım | Değişken adım combo penceresini bozar |
| Kayıt | JSON | Basit, okunabilir, hata ayıklanabilir |
| Kontrol | Klavye + Gamepad | Gamepad bu tür oyunda çok daha iyi hissettirir |

**Mobil kararı: hayır.** Pygame mobilde sorunlu, dokunmatik kontrol bu dövüş sistemine uymaz. PC'ye odaklan; başarılı olursa Godot'ya taşıma ayrı bir proje olur.

---

## 6. SONRAKİ ADIM

Dikey dilim (Bölüm 2) için detaylı tasarım:
- Oda oda level krokisi
- Düşman yerleşimi ve dalgalar
- Gizli sandığın yeri ve ipucu
- Mini-boss davranış ağacı
- Bölümdeki ara sahne panelleri
