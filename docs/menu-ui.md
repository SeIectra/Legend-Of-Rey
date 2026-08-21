# LORE — MENÜ & UI/UX TASARIMI
**GDD Ek G** · v0.1

> "Oyuncunun oyununla ilk etkileşimi arayüzdir. Dağınık, kafa karıştırıcı bir ana menü, oyuncuyu dünyanı keşfetmeye başlamadan önce hayal kırıklığına uğratır."

Ana menü, oyunun **ilk 10 saniyesi**. Steam demosunda oyuncunun gördüğü ilk kare. Ciddiye alınmalı.

---

# 0. AÇILIŞ AKIŞI — INTRO VE KESİNTİSİZ GEÇİŞ ★★★

Oyunun ilk 15 saniyesi. Profesyonel ile amatör arasındaki fark burada görülür.

## 0.1 Ardeko Studios Intro

**Akış (toplam ~4.5 saniye):**

| Süre | Olay |
|---|---|
| 0.0–0.8 sn | Tam siyah. Sessizlik. |
| 0.8 sn | Bir kıvılcım. Tek kare beyaz flaş, sonra sönen bir kor. |
| 0.8–2.0 sn | Kordan **mor alev** doğar, büyür. Işığı yayılır. |
| 2.0–3.5 sn | Logo, alevin ışığıyla karanlıktan **belirir** (fade değil — ışık yayıldıkça görünür hale gelir) |
| 3.5–4.5 sn | Alev söner, logo bir an karanlıkta kalır, kararma |

**Neden mor alev:** Logoyu oyunun görsel imzasına bağlıyor. Oyuncu B3'te mor alevi bulduğunda "bu şeyi ilk açılışta görmüştüm" der. Bedava bir bağ.

**Ses:** Tek bir çakmak/kıvılcım sesi + alçak bir uğultu. Müzik yok. Bir iyi ses, on ortalama sesten iyidir.

**Logo işleme:** Arda'nın mevcut logosu kullanılır. Piksel ızgarasına oturması için tam sayı ölçekle (2× / 3×), `smoothscale` **kullanma**. Logo renkleri paletin dışındaysa sorun değil — intro paletten muaf, tek istisna budur.

## 0.2 Menünün Kurulması

Intro karardıktan sonra ekran **doğrudan menüye kesmez.** Kamera mor alevin çok yakınında başlar ve yavaşça geri çekilir:

1. Ekranı kaplayan mor alev (intro'nun devamı gibi)
2. Kamera geri çekilir → kaide görünür
3. Geri çekilmeye devam → mahzen, zincirler, karakterler
4. Kamera durur → **butonlar tek tek belirir** (her biri 4 kare arayla, alttan yukarı 2px kayarak)

**Süre:** ~3 saniye.

Menü açılan bir ekran değil, **kameranın vardığı bir yer** olur.

## 0.3 YENİ OYUN — Dikey Yolculuk ★★★

Menüden oyuna kesintisiz geçiş. God of War 2'deki koltuktan oynanışa geçen kamera mantığı.

**Sorun:** Menü sahnesi mahzende (derinde), Bölüm 1 köyde (yüzeyde). Düz kayma bu iki mekânı bağlamaz.

**Çözüm:** Kamera mor alevden **yukarı** çıkar.

```
    KÖY / GECE          ← Bölüm 1 başlar
    ─────────────
    toprak, kökler
    ─────────────
    üst kaya katmanı
    ─────────────
    taş tonoz
    ─────────────
    MOR ALEV            ← menü sahnesi
```

**Süre:** 4–5 saniye. Hızlanma → sabit hız → yavaşlama eğrisi (ease-in-out).

**Anlamı:** Menü **gideceğin yer**, oyun **geldiğin yer**. Mor alev sen daha başlamadan orada seni bekliyor. Oyuncu bunu ilk oynayışta anlamaz — B3'te alevi bulunca fark eder.

**Ses:** Yükselirken sesler değişir — mahzen uğultusu azalır, rüzgâr ve gece böcekleri artar. Mekân değişimi kulakla anlaşılır.

## 0.4 DEVAM ET — Aşağı İniş

Aynı geçiş, ters yön. Kamera alevden **aşağı** iner, kaldığın bölüme kadar.

**Ne kadar ilerlediysen o kadar uzun düşersin.** B2'deysen kısa, B15'teysen uzun. İlerlemeyi bedavaya hissettiren bir geçiş.

**Katmanlar bölüme göre değişir:** Katman 1 (taş), Katman 2 (işlenmiş duvar, zincirler), Katman 3 (organik, mor damarlar). Geçerken hangi katmanlardan indiğini görürsün.

## 0.5 HIZLANDIRMA — atlama değil

**Kural: Hiçbir geçiş tuşla ANİDEN kesilmez.** Sert kesme ucuz görünür ve mekân hissini bozar.

Bunun yerine: **tuşa basılı tutunca geçiş 3 kat hızlanır** ve akıcı biçimde varır.

- Kesik yok, ekran kaymıyor, sadece daha çabuk iniyorsun
- İlk kez oynayan tam yaşar
- 20. kez açan bekletilmez
- Ekranın altında küçük bir ipucu belirir (2 saniye sonra): *"Hızlandırmak için basılı tut"*

**Aynı kural şunlara uygulanır:** Ardeko intro, menünün kurulması, dikey yolculuk, ara sahneler.

**İstisna — hızlandırılamayan tek şey:** Bölüm 3'teki "Mor" ara sahnesindeki 2 saniyelik tam karanlık. O sahne zamanlamaya bağlı; hızlandırılırsa etkisi ölür.

## 0.6 Teknik Notlar

**Dikey yolculuk:** Tek bir uzun dikey doku yüzeyi (480 × ~3000 px), 4-5 parallax katmanı. Her karede sadece y-ofset değişir.

**Kritik:** Ofseti **tam sayıya yuvarla** (`int(y)` veya `round(y)`). Ondalık ofset piksel art dokusunu titretir — en yaygın ve en fark edilir hata budur.

**Hız eğrisi:**
```
t = elapsed / duration              # 0 → 1
eased = t * t * (3 - 2 * t)         # smoothstep
y = start + (end - start) * eased
```

**Bulanıklık:** Hızlı geçiş anında hafif dikey motion blur — aynı yüzeyi 3 kez, 1'er piksel kaydırarak, %33 alfa ile üst üste çiz. Ucuz ve etkili.

**Yükleme:** Bölüm 1 verilerini geçiş oynarken arka planda yükle. 4-5 saniye Pygame için fazlasıyla yeterli — oyuncu hiç yükleme ekranı görmez.

---

# 1. ANA MENÜ — SAHNE TASARIMI

## Kompozisyon

```
┌────────────────────────────────────────────────┐
│                                                │
│                              ░░░░              │  ← üst: karanlık tonoz,
│   LEGEND OF                ░░░░░░░░            │     sarkan zincirler
│   ═══════                 ░  MOR   ░           │
│   R E Y                  ░  ALEV  ░            │  ← mor alev, kaidenin üstünde
│                           ░░░░░░░░             │     yumuşak aura
│   ▸ DEVAM ET                ▒▒▒▒               │
│     YENİ OYUN            ╱│    │╲              │  ← Rey ve Ardo, sırt sırta
│     AYARLAR             ╱ │    │ ╲             │     pelerinler rüzgârda
│     EKSTRALAR            REY  ARDO             │
│     ÇIKIŞ                 ▓▓▓▓▓▓               │
│                        ═══════════════         │  ← taş zemin, alevin ışığı
│  v0.1 · Ardeko Studios      ~~~~~~             │     zeminde yansıyor
└────────────────────────────────────────────────┘
```

**Sol üçte bir:** Logo + butonlar. Dikey liste, sola hizalı.
**Sağ üçte iki:** Sahne. Karakterler, alev, mahzen.

**Neden bu düzen:** Batı okuma yönü soldan sağa — göz önce logoya, sonra butona, sonra sahneye gider. Sahne sağda olduğu için butonlarla çakışmaz. Ve karakterler sahnenin "kahramanı" olarak nefes alanına sahip olur.

---

## Sahne Katmanları (arkadan öne)

| # | Katman | İçerik | Hareket |
|---|---|---|---|
| 1 | Derin karanlık | Tonoz kemerleri, silik | Sabit |
| 2 | Arka duvar | Taş dokusu, çatlaklar | Çok yavaş parallax (fare/analog ile ±2px) |
| 3 | Sarkan zincirler | 3-4 zincir, farklı uzunlukta | Yavaş salınım, sinüs (her biri farklı faz) |
| 4 | Toz zerrecikleri | ~40 parçacık | Yukarı doğru yavaş süzülme, mor alevin ışığında parlar |
| 5 | Mor alev + kaide | Ana ışık kaynağı | 6 karelik alev animasyonu + aura nabzı |
| 6 | Aura / ışık halesi | Radyal gradyan | Nefes gibi: 2.5 sn'de bir yavaş büyür/küçülür |
| 7 | Karakterler | Rey ve Ardo, sırt sırta | Boşta animasyonu + pelerin/saç rüzgârı |
| 8 | Zemin | Taş, ıslak yansıma | Alev ışığı zeminde titreşir |
| 9 | Ön toz | ~15 parçacık, bulanık | Kameraya yakın, hızlı geçer (derinlik hissi) |
| 10 | Vinyet | Kenar karartma | Sabit, hafif |

**Toplam maliyet:** 10 katman ama hiçbiri pahalı değil. Katman 3, 4, 6, 9 tamamen **kodla üretilir** — sprite gerekmez.

---

## Karakterlerin Duruşu

**Rey** (solda, hafif öne dönük): Sağ eli kılıcın kabzasında, gevşek. Ağırlığı sol bacağında. Bakışı ileriye — oyuncuya değil, mesafeye. Boynunda **kolye**, hafifçe sallanıyor.

**Ardo** (sağda, sırt sırta): Kolları önde kavuşmuş. Kapüşonlu. Bakışı yana. Daha dik, daha hareketsiz.

**Aralarında 6-8 piksel boşluk var** — dokunmuyorlar. Bu önemli: yakınlık var ama mesafe de var. Hikâyenin başlangıç noktası bu.

**Rüzgâr:** Sağdan sola esiyor. Rey'in saçı ve Ardo'nun pelerini aynı yönde dalgalanıyor — **aynı rüzgâr**. Küçük detay, "birlikteler" mesajı.

### Rüzgâr animasyonu — teknik

Pelerin/saç için ayrı kare çizme. **Dikey dilim kaydırma (vertical slice shear):**

```
Sprite'ı yatay şeritlere böl (her şerit 1-2 piksel).
Her şeridi sinüs dalgasıyla yatay kaydır:
  offset = amplitude * sin(time * frequency + y * wave_length)
Alt şeritler az, üst şeritler çok kayar (kumaş fiziği).
```

Bu, 4 kare pelerin animasyonundan **daha iyi** görünür ve sıfır ek sprite gerektirir. Aynı teknik B'deki bayraklar, örümcek ağları, su yüzeyi için de kullanılır.

---

## Mor Alev — Detay

Menünün görsel kalbi. Üç parça:

**1. Alev gövdesi** — 6 karelik döngü, 8 FPS. Palette `echo_violet` ve iki tonu.

**2. Aura** — Radyal gradyan yüzeyi, `BLEND_RGBA_ADD` ile eklenir. Yarıçap 2.5 saniyelik sinüs ile ±%12 nefes alır. Bu "nefes" hareketi, alevi canlı gösteren şey.

**3. Kıvılcımlar** — Alevden yukarı süzülen 8-12 parçacık. Yavaş, düzensiz. Yükseldikçe sönerler.

**Işık yayılımı:** Alev, sahnedeki her şeyi aydınlatır — karakterlerin bir tarafı mor, diğer tarafı karanlık. Bu, sprite'a ikinci bir "mor kenar" katmanı ile yapılır (silüetin sağ kenarına `echo_violet` ekle, additive).

---

# 2. MENÜNÜN HİKÂYEYLE DEĞİŞMESİ ★★★

En yenilikçi kısım burası. Araştırmadaki örnek: The Last of Us Part II'de ana menü sadece işlevsel değil — duygusal. Durgun bir denizdeki yalnız teknenin hüzünlü görüntüsü hikâyeyle birlikte evrilir ve anlatının ilerleyişini incelikle yansıtır.

Undertale de aynı şeyi yapıyor: ana menü oyun ilerlemesine göre değişiyor.

**LORE'un menüsü ilerlemeye göre 5 aşamadan geçer:**

| Aşama | Koşul | Sahne |
|---|---|---|
| **1 — Yalnız** | Yeni oyun | Sadece **Rey**. Ardo yok. Alev turuncu (normal meşale). Kolye elinde, boynunda değil |
| **2 — İlk Işık** | B3 bitti | Alev **mora döner**. Rey aynı, ama arkasında bir gölge var (belirsiz) |
| **3 — İki Kişi** | B6 bitti (Ardo katıldı) | **Ardo belirir.** Sırt sırta. Mesafeli duruyorlar, 8 piksel |
| **4 — Yaklaşma** | B16 bitti | Mesafe **3 piksele** iner. Ardo'nun eli Rey'in omzunda. Rüzgâr azalmış |
| **5 — Ev** | Oyun bitti | **Cemo da var.** Üçü birlikte. Alev turuncu — sıcak. Rüzgâr durmuş. Zindan değil, gün ışığı |

**Uygulama maliyeti:** Aynı sprite'lar, farklı konumlar + palet değişimi + bir sprite ekleme. Neredeyse bedava.

**Etkisi:** Oyuncu oyunu her açtığında ilerlemesini görür. Ve final sonrası menüyü açtığında **bir şey hisseder**. Bu, jenerik sonrası ödül gibi çalışır.

**Ekstra detay:** Yankı kademen menüde de görünür. SESSIZ'sen alev soluklaşır, fısıltı sesi menüde de kesilir.

---

# 3. BUTONLAR VE ETKİLEŞİM

## Sıralama (UX kritik)

```
▸ DEVAM ET        ← varsayılan seçili, kayıt varsa
  YENİ OYUN
  AYARLAR
  EKSTRALAR
  ÇIKIŞ
```

**Kurallar:**
- Kayıt varsa **DEVAM ET** en üstte ve **önceden seçili**. Oyuncu enter'a basıp devam edebilmeli — düşünmeden.
- Kayıt yoksa DEVAM ET görünmez (gri değil, **yok**). Gri buton "bir şeyi kaçırdım" hissi verir.
- ÇIKIŞ en altta ve seçim listesinden **bir boşlukla ayrılmış** — yanlışlıkla basma riski azalır.

## DEVAM ET kartı

Seçiliyken sağda küçük bir bilgi kartı açılır:

```
┌──────────────────────┐
│  BÖLÜM 7             │
│  "Dar Geçit"         │
│  ─────────────       │
│  Süre    3sa 12dk    │
│  Altın   840         │
│  Yankı   ●●○         │
│  Gizli   6/9         │
└──────────────────────┘
```

**Neden:** Oyuncu 3 hafta sonra döndüğünde nerede kaldığını hatırlamıyor. Bu kart hatırlatır. Ve "6/9 gizli" satırı bir sonraki oturumu şekillendirir.

## YENİ OYUN akışı

Kayıt varken YENİ OYUN'a basılırsa:

```
Mevcut kaydın silinecek.
BÖLÜM 7 · 3sa 12dk

[ İPTAL ]   [ YİNE DE BAŞLA ]
```

İptal **varsayılan seçili**. Yıkıcı eylem asla varsayılan olmaz.

Sonra **karakter seçimi** gelir (aşağıda).

## Buton görsel dili

- Seçili olmayan: soluk gri metin, ikon yok
- Seçili: **beyaz metin + solda ▸ işareti + hafif mor parıltı** (mor alevden geliyormuş gibi)
- Seçim değişiminde: 4 karelik yumuşak geçiş, aynı anda kısa bir "tık" sesi
- Onaylandığında: 6 karelik flaş + daha derin bir "tak" sesi

**Kritik UX kuralı:** Menü **hızlı** olmalı. Hades'te menüler şimşek hızında, güzel düzenlenmiş ve erişilebilir; sonuç olarak arayüze değil aksiyona odaklanıyorsun. Hiçbir menü geçişi 200ms'yi (12 kare) geçmemeli.

---

# 4. KARAKTER SEÇİM EKRANI

Yeni oyunda açılır. Ayrı bir sahne.

```
┌────────────────────────────────────────────────┐
│              KİMİ OYNAYACAKSIN?                │
│                                                │
│     ╔═══════════╗        ┌───────────┐         │
│     ║           ║        │           │         │
│     ║    REY    ║        │   ARDO    │         │
│     ║  (büyük,  ║        │  (küçük,  │         │
│     ║  aydınlık)║        │  karanlık)│         │
│     ╚═══════════╝        └───────────┘         │
│                                                │
│  "Kafasının içinde       "Sessizlikte           │
│   sesler var."            savaşır."             │
│                                                │
│  Hızlı · Kırılgan        Ağır · Dayanıklı      │
│  Yankı: VAR              Yankı: YOK            │
│                                                │
│         [ ◂ ]  Boşluk ile seç  [ ▸ ]           │
└────────────────────────────────────────────────┘
```

**Görsel dil:** Seçili karakter **büyük, aydınlık, animasyonlu**. Diğeri küçük, karanlık, hareketsiz. Bu, "seçmediğin kişi hikâyede olacak" fikrini görsel olarak kuruyor.

**Detay:** Rey seçiliyken arkada fısıltı sesi duyulur. Ardo seçiliyken **tam sessizlik** — oynanış farkını duyarak anlarsın.

**Uyarı metni:** İlk oynayışta küçük bir not: *"İlk kez oynuyorsan Rey önerilir."* Zorlamıyor ama yönlendiriyor.

---

# 5. AYARLAR MENÜSÜ

Sekmeli, ama sekme sayısı az. Üç sekme:

## GÖRÜNTÜ
- Tam ekran / Pencere
- Ölçek (2× / 3× / 4× / Otomatik)
- **Ekran sarsıntısı** (Kapalı / Az / Normal)
- **Renk körü modu** (Yok / Protanopi / Döteranopi / Tritanopi)
- Arayüz boyutu (Normal / Büyük)
- Parlaklık (karanlık oyun — bu şart)

## SES
- Ana ses
- Müzik
- Efektler
- **Yankı fısıltıları** (ayrı kanal — rahatsız edici bulanlar kısabilsin)

## OYNANIŞ
- Dil (Türkçe / English)
- Tuş atama (klavye)
- Tuş atama (gamepad)
- **Alınan hasar** (%50 / %75 / %100 / %150)
- **Düşman hızı** (%75 / %100)
- **Yankı cezası** (Açık / Kapalı)
- **Otomatik combo** (Kapalı / Açık)

**Erişilebilirlik felsefesi:** Zorluk ön ayarları yerine oyun tek tek mekanikleri ayarlamana izin veriyor — "Kolay"ı seçmiyorsun, mücadelenin hangi parçalarını tutacağını seçiyorsun. LORE bunu takip ediyor: "Kolay/Normal/Zor" yok. Oyuncu neyi zor istediğini kendi seçiyor.

**Utandırma yok:** Hiçbir ayar "Kolay Mod" diye etiketlenmez, hiçbir başarım kilitlenmez.

---

# 6. EKSTRALAR

Oyun ilerledikçe açılan bir bölüm. Hollow Knight'ın menü stilleri gibi — küçük ama sevilen bir detay.

- **Galeri** — görülen ara sahne panelleri
- **Bestiary** — öldürülen düşman tipleri, kısa notlarla (kelimesiz: sadece siluet + istatistik)
- **Menü Sahnesi** — kilidi açılan menü varyantları arasında geçiş (aşama 1-5)
- **Müzik Odası** — dinlenen parçalar
- **Mum Bekçisi'nin Mumları** — kaç kez öldüğünü gösteren bir mum duvarı. Rahatsız edici ama dürüst

---

# 7. DURAKLATMA MENÜSÜ

Oyun içinde. **Ana menüden farklı olmalı** — hızlı, minimal, oyunu göstermeye devam eden.

```
      ═══ DURAKLATILDI ═══

        ▸ DEVAM
          EKİPMAN
          AYARLAR
          ANA MENÜ

    Bölüm 7 · Yankı ●●○ · 840 altın
```

**Arka planda oyun görünür** ama karartılmış ve hafif bulanık (bulanıklık için: 4× küçült, 4× büyüt — Gaussian gerekmez).

**Kritik UX:** ANA MENÜ'ye basınca:
```
Ana menüye dön?
İlerlemen kaydedildi. ✓

[ İPTAL ]   [ DÖN ]
```

Oyuncunun kaydedilmemiş ilerleme uyarısıyla karşılaşması bir soru fırtınası yaratır: Kaydetmedi mi? O boss dövüşünü tekrar mı oynayacağım? — Bu tuzağa düşme. **Kaydedildiğini açıkça söyle.**

---

# 8. GENEL UI/UX PRENSİPLERİ

## 8.1 Diegetik olabildiğince

Modern oyuncular sürükleyicilik istiyor, bu da "Diegetik" ve "Meta" UI'ın yükselişine yol açtı — camın üzerindeki düz ikonlar yerine oyun dünyasında var olan öğeler.

LORE'da:
- Yankı göstergesi bir HUD çubuğu değil, **ekran kenarındaki vinyet yoğunluğu**
- Can, kalp ikonu yerine **Rey'in sprite'ındaki değişim** (duruş, nefes hızı) + minimal gösterge
- Combo sayacı ekranda değil, **vuruş sesinin perdesi** ve ekran kenarındaki mor parıltı ile hissedilir. (Sayı isteyenler için ayarlarda açılabilir)
- Kolye pusulası HUD'da değil — **Rey'in boynundaki sprite** parlar

## 8.2 Aşamalı Açığa Çıkarma

Karmaşayı önlemek için Aşamalı Açığa Çıkarma kullanın: bilgiyi sadece ilgili olduğunda gösterin.

- Can göstergesi sadece **hasar aldıktan sonra 3 saniye** görünür
- Altın sayacı sadece **altın toplayınca** belirir
- Yankı göstergesi sadece **kademe değişince** yanıp söner
- Keşif sırasında ekran **tamamen temiz** olabilir

Bu, karanlık atmosferi güçlendirir. Boş ekran = yalnızlık.

## 8.3 Geri Bildirim Kuralları

Her etkileşim **anında, orantılı ve ayırt edilebilir** olmalı:
- Buton seçimi: 1 kare içinde tepki
- Satın alma: farklı ses + altın sayacında animasyon
- Hata (yetersiz altın): kırmızı titreşim + "hayır" sesi
- Menü açılışı: 8 kare fade + hafif zoom

## 8.4 Her Girdi Yöntemiyle Gezilebilir

Oyun menüleri desteklenen her girdi yöntemiyle gezilebilir olmalı.

- Klavye: yön tuşları + Enter + Esc
- Gamepad: D-pad/analog + A + B
- Fare: tıklama **ve** hover
- Üçü de aynı anda çalışsın, mod değiştirme gerekmesin

**Detay:** Fare hareket ederse imleç görünsün, klavye kullanılırsa imleç kaybolsun. Küçük ama profesyonel.

## 8.5 Yükleme Ekranı

Pygame'de yükleme hızlı ama sıfır değil. Boş siyah ekran ucuz durur.

**Çözüm:** Mor alev animasyonu + tek satır. Ve o satır **hikâye parçası** olsun — zindan hakkında kısa, şiirsel bir cümle. 20-30 farklı satır, rastgele. Oyuncu yükleme ekranını okumak ister.

---

# 9. TÜRKÇE FONT — KRİTİK

Prototipte "Asagi bakma. Ustunden gec." yazıyor. Bu **kabul edilemez**.

**Gerekli karakterler:** ğ Ğ ü Ü ş Ş ı I i İ ö Ö ç Ç

**Özellikle dikkat:** Türkçe'de **ı** (noktasız) ve **i** (noktalı) farklı harfler, ve büyük halleri **I** ve **İ**. Çoğu font bunu bozar. `str.upper()` kullanırsan Python `i` → `I` yapar, Türkçe'de `İ` olmalı. Menüde büyük harf kullanacaksan **özel bir upper fonksiyonu** yaz.

**Öneri:** Türkçe destekli ücretsiz piksel fontlar mevcut. Yoksa mevcut fonta 12 karakter eklemek yarım günlük iş — ve bütün oyunu etkiliyor.

---

# 10. UYGULAMA SIRASI

1. **Font (Türkçe)** — her şeyden önce
2. Menü iskeleti: butonlar, gezinme, geçişler (sahne yok, düz arka plan)
3. Ayarlar menüsü (işlevsel, çirkin olabilir)
4. Kayıt/yükleme + DEVAM ET kartı
5. Sahne katmanları: arka duvar → alev → karakterler → parçacıklar
6. Rüzgâr shear animasyonu
7. Aura nabzı + ışık yayılımı
8. **Ardeko Studios intro** (bölüm 0.1)
9. **Menünün kurulması** — kamera geri çekilir, butonlar belirir (0.2)
10. **Dikey yolculuk** — yukarı (yeni oyun) ve aşağı (devam et) (0.3, 0.4)
11. **Hızlandırma sistemi** — basılı tutunca 3× (0.5)
12. Karakter seçim ekranı
13. Duraklatma menüsü
14. Menünün ilerlemeye göre değişmesi (5 aşama)
15. Ekstralar
16. Yükleme ekranı satırları (dikey yolculuk sayesinde nadiren görünecek)

**1-4 işlevsel katman, 5-16 cila.** İşlevsel olan önce bitmeli — güzel ama kullanılamaz bir menü, çirkin ama hızlı bir menüden kötüdür.

---

# 11. TEKNİK NOTLAR (Pygame)

**Aura/glow:** Gerçek bloom pahalı. Ucuz taklit:
```
1. Alev sprite'ını al
2. 4× küçült (scale)
3. 4× büyüt (smoothscale) → yumuşak, bulanık hale
4. BLEND_RGB_ADD ile ana yüzeye ekle
```
Üç satır, gerçek glow'a çok yakın sonuç. **Not:** Bu, oyun içi piksel art için değil — sadece ışık/aura katmanı için. Sprite'lara asla `smoothscale` uygulama.

**Parallax:** Fare pozisyonu (veya analog çubuk) ile katmanları ters yönde ±2-4 piksel kaydır. Menü "canlı" hisseder, maliyet sıfır.

**Menü sahnesi bir kez üretilip önbelleğe alınsın.** Statik katmanlar (duvar, tonoz) her karede yeniden çizilmesin — tek bir yüzeye pişir, sadece hareketli katmanları üstüne çiz.

**Geçişler:** Sahneler arası geçiş için basit bir "karartma + açılma" yeterli değil. Daha iyisi: **mor alev büyür, ekranı kaplar, sonra küçülür ve yeni sahne belirir.** Tematik ve hatırlanabilir.

**Kayıt formatı:** JSON. Ve **her zaman iki dosya tut** — `save.json` ve `save.bak.json`. Yazma sırasında çökme olursa yedekten dön. Oyuncunun 3 saatlik ilerlemesini kaybetmek affedilmez.
