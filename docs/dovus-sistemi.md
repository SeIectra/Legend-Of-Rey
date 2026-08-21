# LORE — Dövüş Sistemi & Game Feel
**GDD Ek A** · v0.1

Bütün süreler **60 FPS'te kare** cinsinden. Pygame'de `dt` yerine kare sayacı kullan — dövüş sisteminde kare hassasiyeti şart.

---

## 1. TEMEL ZİNCİR

Tek saldırı tuşu. Üç vuruşluk zincir:

| Vuruş | Ön (windup) | Aktif | Son (recovery) | Hasar | Geri itme |
|---|---|---|---|---|---|
| 1 | 4 kare | 3 kare | 8 kare | 10 | Az |
| 2 | 5 kare | 3 kare | 9 kare | 12 | Az |
| 3 (bitirici) | 8 kare | 5 kare | 16 kare | 25 | Çok |

**Zincir penceresi:** Bir vuruşun aktif karesi bittikten sonra **12 kare** içinde tekrar basarsan zincir devam eder. Basmazsan zincir sıfırlanır.

**Neden 12 kare (0.2 sn):** Cömert ama sonsuz değil. Oyuncu ritmi hisseder, tuşa basmak zorunda olduğunu bilir, ama zamanlamaya köle olmaz. Hızlı-akıcı dövüşün formülü budur.

**İptal (cancel) kuralları — akıcılığın kalbi:**
- Vuruş 1 ve 2'nin recovery'si **kaçınma ile iptal edilebilir**
- Vuruş 3'ün recovery'si iptal edilemez → bitiriciyi savurmak bir karardır, bedeli var
- Bir düşman öldüğü anda **bütün recovery iptal olur** (kill cancel) → kalabalıkta kesintisiz akış

Kill cancel tek başına oyunu on kat iyi hissettirir. Kalabalık dövüşün "biçip geçme" hissi buradan gelir.

---

## 2. HAVAYA KALDIRMA (Juggle)

**Yukarı + saldırı** = kaldırıcı. Düşman havalanır.

- Havadaki düşman **3 vuruş** yiyebilir, sonra yere düşer
- Her vuruşta düşme hızı biraz artar (sonsuz juggle engellenir)
- Havadayken hasar **%20 fazla** → riskli oynamanın ödülü
- Havadaki düşman diğer düşmanlara çarparsa onları da sersemletir

**Neden var:** Dan the Man'in karakteri buydu. Ayrıca oyuncuya "kendi tarzını bulma" alanı açar — kimisi yerde combo yapar, kimisi havada.

---

## 3. KAÇINMA (Dodge)

- **6 kare** dokunulmazlık, **18 kare** toplam süre
- Kaçınma sonrası **9 kare** içinde saldırırsan → **karşı vuruş**, %30 fazla hasar
- Bekleme süresi (cooldown): 24 kare

**Neden karşı vuruş var:** Kaçınmayı savunma değil *saldırı hazırlığı* yapar. Oyuncu kaçarak değil, atarak hayatta kalır. Hızlı-akıcı kimliğe uygun.

---

## 4. COMBO SAYACI

Ekranın sağ üstünde. Vuruş arası **90 kare** (1.5 sn) sessizlik geçerse sıfırlanır.

| Eşik | Ödül |
|---|---|
| 5 | Altın kazancı ×1.2 |
| 10 | Altın ×1.5, hafif can yenilenmesi |
| 20 | Altın ×2, **Yankı bir kademe iyileşir** |

**Kritik bağlantı:** 20 combo Yankı'yı iyileştiriyor. Yani iyi oynayan oyuncu lanetini kontrol altında tutar; kötü oynayan körleşir. Ölüm cezası ve dövüş becerisi tek döngüde birleşiyor.

---

## 5. GAME FEEL PAKETİ

Kalite algısının çoğu burada. Hepsi ucuz, hepsi zorunlu.

### Hitstop (vuruş donması)
Vuruş anında **her iki tarafı da** dondur:

| Olay | Süre |
|---|---|
| Normal vuruş | 3 kare |
| Bitirici | 7 kare |
| Boss vuruşu | 9 kare |
| Öldürücü darbe | 12 kare |

Pygame'de: `hitstop_frames` sayacı, sıfırdan büyükken fizik ve animasyon güncellemesini atla, çizimi sürdür. 15 satır kod, en büyük his farkı.

### Ekran sarsıntısı
- Normal vuruş: 2 piksel, 4 kare
- Bitirici: 5 piksel, 8 kare
- Boss vuruşu / patlama: 9 piksel, 12 kare
- **Bozunum eğrisi:** doğrusal değil, üstel (`amp *= 0.85` her kare). Doğrusal sarsıntı ucuz durur.
- **Ayar menüsünde kapatılabilir olsun** — erişilebilirlik ve mide bulantısı.

### Vuruş flaşı
Düşman sprite'ı **2 kare** tamamen beyaz. `pygame.Surface` üzerine `BLEND_RGB_ADD` ile maske. Tek satırlık iş, devasa fark.

### Geri itme (knockback)
Vuruş yönünde itme + hafif yukarı bileşen. Bitirici düşmanı duvara çarparsa **ekstra hasar + sersemleme**. Arena tasarımı böylece anlam kazanır.

### Vuruş efekti (slash)
2–3 kare süren yarım ay çizimi. Silaha göre farklı renk/uzunluk. Piksel artta 4 kare yeter.

### Kamera
- Hedef takip, **yumuşatma katsayısı 0.12**
- Saldırı yönüne **12 piksel** kayma (look-ahead)
- Boss girişinde kısa zoom-out

### Ses (game feel'in yarısı)
- Vuruş sesi **katmanlı**: temas + metal + düşman tepkisi
- Combo yükseldikçe **perde hafif yükselsin** (her 5 combo'da +%3) → ilerleme kulakla hissedilir
- Yankı açıkken tüm sesler alçak geçiren filtreden geçsin (Pygame'de: önceden filtrelenmiş ikinci ses seti)
- Ayak sesi zemine göre değişsin (taş, su, çakıl)

---

## 6. DÜŞMAN TARAFI

**Tell (ön işaret) kuralı:** Her düşman saldırısı en az **14 kare** öncesinden okunabilir olmalı — poz değişimi + renk vurgusu. Okunamayan hasar, oyuncuya haksızlık gibi gelir ve kaliteyi düşürür.

**Saldırı hakkı sistemi:** Aynı anda en fazla **2 düşman** saldırabilir. Diğerleri etrafta dolanır, sırasını bekler. Bu, kalabalık dövüşü kaotik olmaktan çıkarıp okunabilir yapan tek en önemli kuraldır — Batman: Arkham, Assassin's Creed, hepsi bunu kullanır.

**Sersemleme (stagger):** Her düşmanın bir poise değeri var. Yeterli vuruş yerse sendeler, saldırısı iptal olur. Zırhlı düşmanlarda yüksek → combo'yu kırar, katman 2'nin kimliğini kurar.

---

## 7. OYUNCU AFFI (Forgiveness)

Kaliteli oyunlar oyuncuya sessizce yardım eder:

- **Coyote time:** Platformdan düştükten sonra **6 kare** daha zıplayabilir
- **Girdi tamponu:** Saldırı/zıplama tuşu **8 kare** önceden basılırsa hafızada tutulur, uygun anda çalışır
- **Son şans:** Can %15'in altındayken öldürücü darbe alırsan, **1 can ile hayatta kal** — bölüm başına bir kez
- **Kaçınma cömertliği:** Dokunulmazlık, animasyonun görsel başlangıcından 2 kare önce başlar

Hiçbiri oyuncuya söylenmez. Sadece oyun "adil" hisseder.

---

## 8. REY / ARDO FARKI

| | Rey | Ardo |
|---|---|---|
| Hareket hızı | 1.15× | 0.9× |
| Can | 80 | 120 |
| Zincir penceresi | 14 kare (cömert) | 10 kare (sıkı) |
| Kaçınma | 2 şarj, kısa mesafe | 1 şarj, uzun mesafe |
| Bitirici | Hızlı, çok vuruşlu | Tek, ağır, geniş alan |
| Yankı | Var | Yok |
| Özel | 20 combo'da Yankı iyileşir | Kaçınma sonrası karşı vuruş %60 hasar (Rey'de %30) |

**Tasarım niyeti:** Rey bilgiyle ve akışla kazanır, Ardo zamanlamayla ve dayanıklılıkla. Ardo'nun Yankı eksikliği, karşı vuruş gücüyle telafi edilir — yardım almıyorsa okumayı iyi bilmeli.

---

## 9. UYGULAMA SIRASI

Bu belgeden koda geçerken sıra önemli:

1. Temel zincir + iptal kuralları
2. **Hitstop** (en yüksek getiri)
3. Vuruş flaşı + ekran sarsıntısı
4. Kill cancel
5. Kaçınma + karşı vuruş
6. Saldırı hakkı sistemi (düşman AI)
7. Combo sayacı + ödülleri
8. Juggle
9. Oyuncu affı katmanı
10. Ses katmanları

İlk dördü bittiğinde oyun zaten "iyi" hissedecek. Gerisi derinlik.
