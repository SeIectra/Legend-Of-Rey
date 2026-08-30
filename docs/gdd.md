# LEGEND OF REY (LORE) — Game Design Document
**v0.1 — Tasarım Aşaması** · Ardeko Studios · Pygame

---

## 1. TEK CÜMLE

Kafasının içindeki sesler yüzünden lanetli sayılan Rey, kaçırılan kardeşi Cemo'yu kurtarmak için zindana iner — ve o sesler ona yardım ederken, aslında onu çağırıyordur.

## 2. TEMEL KİMLİK

| | |
|---|---|
| **Tür** | Yandan görünümlü aksiyon-RPG |
| **Referans** | Forgotten Warrior (oynanış), Dan the Man (anlatım) |
| **Motor** | Pygame |
| **Dövüş** | Hızlı ve akıcı — combo zinciri, kalabalık düşman |
| **Temel duygu** | Keşif + güçlenme |
| **Yapı** | Doğrusal, 18 bölüm |
| **Görsel** | Piksel art (32x32 karakter, 16x16 tile) |
| **Anlatım** | Diyalogsuz — statik panel, jest, ikon balonu |

## 3. KARAKTERLER

- **Rey** — Yankı taşıyan genç kadın. Hızlı, kırılgan, bilgiyle avantaj kurar.
- **Ardo** — zindanın derinindeki bir şeyin peşindeki yabancı. Yavaş, dayanıklı, zamanlamayla avantaj kurar. Yankı'sı yok.
- **Cemo** — Rey'in küçük kardeşi. Pasif kurban değil: kaçmayı dener, iz bırakır.

**Karakter seçimi:** Oyun başında Rey ya da Ardo. Seçmediğin, ara sahnelerde havalı girişi yapan taraf olur.

## 4. YANKI SİSTEMİ (Ana mekanik)

Rey'in laneti. Tutorial, ipucu ve bilgi bu sesle gelir — diegetik UI.

**Üç kademe:**
1. **Berrak** — düşman siluetleri duvar ardından görünür, gizli geçitler parlar, bulmaca ipucu verir
2. **Bulanık** — sadece yakın mesafe, uyarı var detay yok
3. **Sessiz** — hiç yardım yok (Ardo'nun standart oynanışı)

**Kademe kaybı:** ölünce bir kademe düşer. **Dip: Sessiz** — daha aşağı inmez, ölüm sarmalı engellenir.
**Kademe kazanımı:** kontrol noktaları ve nefes bölümleri (B4, B8, B12).
**Bedel:** aktif kullanımda ekran kenarı kararır, ses boğuklaşır, savunma düşer.
**Teşvik:** Yankı kapalı geçilen bölümler daha çok ödül verir → ceza, meydan okumaya dönüşür.

**Twist (B14):** Yankı lanet değil, aşağıdaki şeyin sesidir. Hep yardım ediyordu çünkü Rey'i çekiyordu.

## 5. ÖLÜM

- Kontrol noktasından devam (bölüm başı değil)
- Altının %30'u düşer — yerde kalır, gidip alınabilir
- Yankı bir kademe zayıflar
- **Düşmanlar geri gelir, bulmacalar gelmez**
- Yetenekler, ekipman, açılan içerik kalıcı

## 6. GÜÇLENME

**Ana sistem: Ekipman.** Kural — sayı değil, oynanış değişir.

| Slot | Ne belirler | Örnekler |
|---|---|---|
| **Silah** | Dövüş ritmi | Hançer (uzun combo, kısa menzil) · Kılıç (dengeli) · Balta (yavaş, zırh deler) |
| **Zırh** | Risk profili | Hafif (hızlı kaçınma, az can) · Ağır (yavaş, vuruş yerken combo bozulmaz) |
| **Tılsım** | Bir kuralı bozar | "Combo 5+ yakar" · "Yankı zayıfken hasar artar" · "Kaçınmada zaman yavaşlar" |

**Dağıtım:** Her bölüm bir parça garanti eder (ana yol), bir parça saklar (bulmaca arkası). Berrak Yankı gizli olanı gösterir → üç sistem tek halkada birleşir.

**İkincil:** Yetenek ağacı (3 dal × 4 seviye) · Kalıcı buluntular (+1 combo penceresi, +5 can)

## 7. DÜŞMAN EKOSİSTEMİ

Katman geçişleri keskin değil — sızarak karışır.

### Katman 1 · Üst Zindan (B1–B6) — Çürüyenler
*Soru: combo kurmayı öğren*
- **Sürüklenen** — yavaş, tek saldırı. Combo hedef tahtası
- **Tırmanan** — duvar/tavan, yukarıdan atlar. Dikey farkındalık
- **Şişkin** — ölünce patlar. Konumlandırma önem kazanır

### Katman 2 · Orta Zindan (B7–B13) — Lanetli Muhafızlar
*Soru: combo'yu kırmayı öğren*
- **Kalkanlı** — önden vurulmaz, arkaya geç
- **Mızraklı** — uzun menzil, yaklaşmayı engeller
- **Okçu** — uzaktan bozar, önce susturulmalı
- **Komutan** — takviye çağırır, kalabalık yönetimi

### Katman 3 · Derin Zindan (B14–B18) — Yankı'nın Çocukları
*Soru: yardımcı sisteminin ihanetiyle yüzleş*
- **Sessiz** — Yankı onu göstermez
- **Yankılayan** — sesini taklit eder, sahte ipucu verir
- **Bölünen** — vurunca ikiye ayrılır; combo sana karşı çalışır

## 8. BOSS YAPISI

**4 büyük boss** (hikâye dönüm noktalarında) + **her bölümde mini-boss**

- Mini-boss: mevcut düşmanın büyütülmüş hali, bir ek hamle. Öğretmez, sınar. Ucuz.
- Boss: kendi arenası, kendi animasyon seti, faz geçişleri, ezberlenecek tell'ler. Maliyeti 10 kat.

| Boss | Bölüm | Rol |
|---|---|---|
| 1 | B6 | Ardo'yla ilk beraber dövüş |
| 2 | B13 | Cemo kovalamacası |
| 3 | B14 | Yankı'nın kaynağı |
| 4 | B18 | Final — sessizlikte, yardımsız |

## 9. MEKANİK HAVUZU

Kural: **yeni mekanik + eski mekanik = yeni bulmaca**

| # | Mekanik | Tanıtım |
|---|---|---|
| 1 | Yankı Görüşü | B1 |
| 2 | Meşale / Karanlık | B3 |
| 3 | Su seviyesi (vana) | B5 |
| 4 | Ağırlık plakaları | B6 |
| 5 | Yankı Rezonansı | B8 |
| 6 | Team-up fırlatma | B9 |
| 7 | Ayna & ışık | B11 |
| 8 | Zaman kapıları | B13 |
| 9 | Sessizlik / gürültü | B15 |
| 10 | İkili kontrol | B17 |
| 11 | **Sürülebilir düzenek** | B12 |

> **11. madde 30.08.2026'da eklendi.** Arda sordu: *"jetpack, helikopter,
> araba veya tank gibi sürülebilir bişey ekleyip bir bölümü de öyle
> oynatmak istiyorum ama çok absürt mü kaçar?"*
>
> Dördü de reddedildi — sorun "araç" değil **çağ**: zindanda meşale,
> zincir, kafes ve anahtar var; oraya bir tank koymak sürpriz değil
> tutarsızlık olurdu. Ama istek doğruydu: oyun kendi döngüsünü zaten
> dört kez bilerek kırıyor (B4/B8/B12 nefes, B15 gizlilik, B17 ikili
> kontrol). Değişen tek şey araç oldu.
>
> Uygulaması: **Ardo'nun kuyuya kurduğu iniş kafesi** (B12). Tek
> kontrol fren; duvarlardaki izler yalnızca yavaşken okunuyor. Ceza
> yok, ölüm yok — değişen tek şey onun ne kadarını gördüğün. Araç bir
> nefes bölümünü bozmuyor çünkü **onun bıraktığı bir şey**: binmek
> zaten yakınlık.
>
> İkinci uygulaması için aday B14 sonrası: *Yankı seni taşıyor* —
> jetpack'in dünya içindeki karşılığı. Uçmuyorsun, **çekiliyorsun**;
> B14 twist'inin fiziksel hali. Sırası gelince karar verilecek.

## 10. BÖLÜM AKIŞI (Özet)

| # | Bölüm | İçerik |
|---|---|---|
| 1 | Köy | Kolye, Cemo'nun kaçırılışı, tutorial |
| 2 | İlk İniş | Combo, kaçınma, ilk gizli geçit |
| 3 | Meşale Mahzeni | Karanlık, risk/ödül |
| 4 | Kayıt Odası ★nefes | Yetenek ağacı açılır, kelimesiz günlük |
| 5 | Sular | Vana bulmacası |
| 6 | ARDO | Havalı giriş, ilk team-up, **BOSS 1** |
| 7 | Dar Geçit | İlk temas — el tutma |
| 8 | Ateş Başı ★nefes | Rezonans öğrenilir, Yankı ilk kez Ardo hakkında konuşur |
| 9 | Çan Kulesi | Rezonans bulmacası, fırlatma mekaniği |
| 10 | Ayrılık | Yalnızlık, **Yankı ilk kez yalan söyler** |
| 11 | Ayna Salonu | Işık bulmacası, Yankı'ya güvenememe |
| 12 | Mektup ★nefes | Ardo'nun izleri — yoklukta yakınlık |
| 13 | Cemo | Kovalamaca, **BOSS 2** |
| 14 | Yankı'nın Kaynağı | Twist, **BOSS 3**, Yankı tersine döner |
| 15 | Sessizlik | Gizlilik bölümü, dövüşsüz geçilebilir |
| 16 | Sırt Sırta | Rey Ardo'yu kurtarır, kalp balonu |
| 17 | İkili Kule | Karakter geçişi, karşılıklı bağımlılık |
| 18 | Son | Yankı susturulur, **BOSS 4**, mutlu son |

## 11. ROMANTİK YAY

Hiçbiri diyalogla anlatılmaz — ya jest ya mekanik.

| Bölüm | An | Anlatım |
|---|---|---|
| B6 | İlk karşılaşma | Bakışma, soru işareti |
| B7 | İlk temas | Elden çekme, bir saniye fazla |
| B8 | Kırılganlık | Yara sarma |
| B9 | Güven | Fırlatma — kendini ona bırakıyorsun |
| B12 | Özlem | Yoklukta bırakılmış izler |
| B16 | Eşitlik | Sen onu kurtarıyorsun |
| B17 | Bağımlılık | Biri olmadan geçilmiyor |
| B18 | Kapanış | Üçlü son panel |

## 12. AÇIK KALAN KARARLAR

- Game feel paketi: hitstop süresi, ekran sarsıntısı eğrisi, vuruş flaşı
- Combo sistemi detayı: kaç vuruş, pencere kaç kare, bitirici var mı
- Rey/Ardo istatistik farkları (sayısal)
- Ses tasarımı yaklaşımı
- Ekonomi: altın kaynakları ve fiyat eğrisi
- Kontrol şeması (klavye / gamepad / mobil?)
