# BÖLÜM 3 — "MEŞALE MAHZENİ"
**Detaylı Tasarım** · GDD Ek F

**Hedef süre:** 11–14 dakika
**Zorluk:** 3/10
**Tema:** Işık bir kaynaktır. Ve karanlıkta bir şey seni izliyor.

---

## BÖLÜMÜN AMACI

B2 dövüşü öğretti. B3 **oyuncuyu ilk kez seçim yapmaya zorlar** — ve oyunun doğaüstü katmanını açar.

Üç yeni şey tanıtılır:
1. **Meşale ekonomisi** — ışık taşımak, dövüşmekle çelişir
2. **Mor Alev** — oyunun ilk doğaüstü nesnesi, kalıcı ışık ama bedelli
3. **Mum Bekçisi** — konuşmayan, savaşmayan, ticaret yapan bir varlık. Dünyanın kendi kuralları olduğunun kanıtı

Ve hikâye olarak: Rey ilk kez **zindanın doğal olmadığını** anlar.

---

# ARA SAHNE 1 — "İNİŞ" (bölüm açılışı, ~8 saniye)

**Panel A.** Rey merdivenin başında. Elinde B2'den kalan meşale. Aşağısı görünmüyor — kamera aşağı doğru pan yapar, siyahlığa girer, hiçbir şey yok.

**Panel B.** Meşale ışığı. Sadece 3 tile'lık bir daire. Rey'in yüzü yarı aydınlık.

**Panel C.** Yankı fısıldar. Ekranda dalga. Rey duraksar, sonra iner.

*Kelime yok. Sadece ışığın küçüklüğü ve karanlığın büyüklüğü.*

**Teknik:** Panel A'da kamera aşağı pan + ışık yarıçapı 0'a düşer. Bu tek hareket "buranın derinliği" hissini kurar.

---

# ODA AKIŞI

### ODA 1 — Işığın Kuralı (90 sn)

Dar, uzun bir koridor. Duvarda **sönmüş meşale yuvaları** — düzenli aralıklarla. Biri yanıyor.

**Öğretim:**
- Meşaleyi taşırken **sadece tek elle** savaşabilirsin: combo 3'lü değil, 2'li. Bitirici yok.
- Meşaleyi yuvaya koyabilirsin → iki elin serbest, ama ışık orada kalır
- Meşaleyi **fırlatabilirsin** → ışık gittiği yerde kalır, sen karanlıkta

Koridorda 2 Sürüklenen var ama **ışık dairesinin dışında**. Oyuncu onları duyar, görmez. İlk gerçek gerilim anı.

**Tasarım notu:** İlk düşmanı öldürmek için meşaleyi bırakmak *zorunda* değil — ama tek elle dövüşmek yavaş. Oyuncu kendi kararını versin. Her iki yol da çalışsın.

---

### ODA 2 — Karanlık Geçiş (2 dk)

Büyük, boş görünen bir mahzen. Meşale ışığı 3 tile — oda 20 tile.

**Yeni mekanik: SES HARİTASI**
Yankı'yı aktive edince ekranda **1 saniyelik bir "ses dalgası"** yayılır. Duvarlar, düşmanlar, platformlar bir an için beyaz konturla görünür ve söner. Sonar gibi.

Bu, "Yankı = bilgi" fikrini **görsel bir mekaniğe** çeviriyor. Ve karanlıkta gerçekten kullanışlı.

**Bedeli:** Ses dalgası düşmanları da uyandırır. Gördüğün her şey seni gördü.

**Oda yapısı:** 4 platform, arada boşluk. Karanlıkta zıplamak = körlemesine. Ses haritası olmadan geçilebilir ama zor.

**Ödül:** Odanın kenarında ilk **sandık** — 35 altın.

---

# ARA SAHNE 2 — "DUVARDAKİLER" (~6 saniye)

Rey bir duvara yaklaşır. Meşale ışığı duvarı yalar.

**Panel A.** Duvarda kazınmış işaretler. Onlarca. Yüzlerce. Çetele gibi — birileri gün saymış.

**Panel B.** Kamera yavaşça sağa kayar. Çeteleler devam ediyor. Ve devam ediyor.

**Panel C.** Çeteleler biter. Son işaret yarım kalmış.

*Balon: yok. Rey'in eli duvara dokunur, geri çeker.*

**Neden güçlü:** Kimse ölmedi diye bir şey söylemiyoruz. Oyuncu kendi hesabını yapıyor. Ve "yarım kalmış çetele" hepsinden fazla konuşuyor.

---

### ODA 3 — Yuvalar Bulmacası (2.5 dk)

Beş meşale yuvası, çapraz yerleşimli. Yanan tek meşale sende.

**Bulmaca:** Bir meşaleden diğerini yakabilirsin ama **meşale taşırken zıplayamazsın** (iki elin de dolu — biri meşale, biri tırmanmak için değil). Yani ışığı yukarı taşımak için fırlatman gerekiyor.

Fırlatılan meşale: bir yay çizer, düştüğü yerde yanar. Isabetli fırlatmak = yeni ışık noktası.

**Çözüm zinciri:** Yuvaları sırayla yakarak odanın haritasını açarsın. Her yakılan yuva kalıcı ışık.

**Katman:** 3 Tırmanan tavanda. Işık yaklaşınca **kaçarlar** — ışıktan korkuyorlar. Bu, ışığı silah yapıyor.

**Ödül:** Beş yuvanın hepsi yanınca duvarda gizli bir kapı açılır (ısıyla açılan mekanizma).

---

### ODA 3-A — GİZLİ: MUM BEKÇİSİ (2 dk) ★★★

Küçük, sıcak, garip bir oda. Yüzlerce mum. Ortada oturan bir figür.

**MUM BEKÇİSİ:**
- İnsan silueti ama yüzü yok — kukuletanın altı boş, sadece iki mum alevi göz yerinde
- Hareket etmez. Sadece başını çevirir.
- Saldırmaz. Saldırılamaz (vuruşlar geçer, hasar yok)
- Konuşmaz

**Ticaret sistemi:** Önünde bir tabak. Altın koyarsın, karşılığında bir şey alırsın:
- 40 altın → yeni meşale
- 120 altın → **"Sönmez Fitil"** (meşale artık kendi kendine sönmüyor)
- 200 altın → Mum Bekçisi sana bir mum verir. Bu mum, **öldüğün yerde yanar** ve altınını korur

**Tasarım niyeti:** Hollow Knight dersi — düşmanca bir dünyada düşman olmayan varlıklar, yalnızlığı azaltmaz, **derinleştirir.** Bekçi sana yardım eder ama seninle ilgilenmez. Sen buradan geçen binlerinci kişisin.

**Detay:** Odanın duvarında, mumların arasında **sönmüş mumlar** var. Her sönmüş mum bir ölü. Sayısı korkunç.

**Tekrar görünür:** Mum Bekçisi B7, B12 ve B16'da tekrar çıkar. Her seferinde biraz daha derinde, biraz daha az mumla.

---

### ODA 4 — Sürünen Karanlık (2 dk)

Koridor. Ama bu sefer karanlığın kendisi hareket ediyor.

**Yeni düşman varyantı: GÖLGE SÜRÜKLENEN**
- Sadece karanlıkta var. Işığa girince **donar ve saldıramaz** (ama ölmez)
- Işıktan çıkınca tekrar canlanır
- Öldürmek için ışıkta dövmelisin

**Oynanış sorusu:** Meşaleyi tutarken tek elle mi dövüşeceksin, yoksa meşaleyi yere koyup dar bir ışık dairesinde mi savaşacaksın?

İkincisi doğru cevap — ve oyuncu bunu kendi bulur. Bu bir "aha" anı.

**Yoğunluk:** 4 Gölge Sürüklenen, dalgalar halinde.

---

# ARA SAHNE 3 — "MOR" (~10 saniye) ★★★ bölümün kalbi

**Panel A.** Rey bir kemerin altından geçer. Meşalesi titreşir. Sonra **söner.**

**Panel B.** Tam karanlık. 2 saniye. Hiçbir şey. Sadece nefes sesi.

**Panel C.** Uzakta bir ışık belirir. **Mor.** Titremiyor, çıtırdamıyor — sadece duruyor.

**Panel D.** Kamera yavaşça yaklaşır. Mor alev bir taş kaidenin üstünde yanıyor. Etrafında donmuş mumlar, buz gibi.

**Panel E.** Rey elini uzatır. Alev **soğuk.** Nefesi buğulanır.

**Panel F.** Yankı **bağırır** — ilk kez fısıltı değil. Ekran sarsılır. Rey geri çekilir.

*Ve sonra ses susar. İlk kez tamamen susar.*

**Teknik:** Panel B'deki 2 saniyelik tam karanlık kritik. Oyuncu ekranın bozulduğunu sanmalı. Sonra mor ışık gelmeli.

---

### ODA 5 — MOR ALEV (3 dk)

**MOR ALEV MEKANİĞİ:**

Alevi alabilirsin. Aldığında:

**Artılar:**
- **Sönmez.** Kalıcı ışık kaynağı
- Işık yarıçapı normal meşalenin 2 katı
- Yankı berraklaşır — bir kademe yükselir ve orada kalır
- Gölge düşmanlar ona yaklaşamaz

**Eksiler:**
- Yankı **sürekli konuşur** — sessizlik yok. Arka planda hep fısıltı
- Yankı'nın yalan söyleme ihtimali artar (B10'da patlayacak tohum)
- Mum Bekçisi seninle **ticaret yapmaz** (mor alev taşıyanı tanımıyor)
- Bazı düşmanlar seni daha uzaktan fark eder

**VE ASIL SEÇİM:** Almak zorunda değilsin.

Alevi bırakıp normal meşaleyle devam edebilirsin. Oyun bunu **hiç söylemez** — sadece iki yol da açık kalır. Bölüm sonu ekranında "Mor Alev: alındı / bırakıldı" yazar. Oyuncu ikinci seçeneğin var olduğunu o zaman anlar.

**Uzun vadeli etki:** Bu karar B14'ün twist sahnesini değiştirir. Alevi taşıyanlar için ihanet daha ağır. Bırakanlar için "sezmiştim" anı.

**Tasarım felsefesi:** İyi oyunlar oyuncuya güç verir ve bedelini gizlemez. Ama bedeli **hemen** hissettirmez — yavaşça sızdırır.

---

### ODA 6 — Alev Sınavı (2 dk)

Mor alevle (veya meşaleyle) geçilecek son bölüm. Uzun, dikey, aşağı inen bir kuyu.

- Platformlar arasında geniş boşluklar
- Duvarda Gölge Sürüklenenler
- Aşağıdan yukarı esen bir hava akımı — **meşaleyi söndürüyor** (mor alev etkilenmiyor)

**Yani:** Mor alevi aldıysan burası kolay. Almadıysan zorlu ama geçilebilir — hava akımının olmadığı köşeleri bulman gerekiyor.

**İki farklı oynanış, aynı oda.** Bu, seçimin gerçek olduğunu kanıtlıyor.

---

### ODA 7 — MİNİ-BOSS: "SÖNMÜŞ OLAN" (3 dk)

Geniş, dairesel arena. Ortada büyük bir mangal — **sönmüş.**

**Boss tasarımı:** Eskiden Mum Bekçisi gibi bir varlıkmış. Ama mumları sönmüş, kendisi bozulmuş. Kukuletası yırtık, gözlerinde alev yok — sadece boşluk.

**Üç hamlesi:**
1. **Karanlık Dalgası** — arenadaki tüm ışıkları söndürür (2 saniye tam karanlık). 20 kare tell: kollarını açar
2. **Sürükleme** — hızla yaklaşır, tek vuruş. Kaçınmayla geçilir
3. **Mum Çağrısı** — üç sönmüş mum belirir, Gölge Sürüklenen doğurur

**Arena mekaniği:** Ortadaki mangalı yakabilirsin (meşale/mor alev ile). Yanan mangal:
- Boss'un Karanlık Dalgası'nı **iptal eder**
- Ama boss mangalı söndürmeye çalışır

**Yani dövüş üç katmanlı:** Boss'a vur, mangalı yak, mangalı koru.

**Zayıflık:** Mangal yanarken boss sersemler — combo penceresi. Bunu keşfeden oyuncu ödüllendirilir.

**Ödül:** 70 altın + **"Fener" tılsımı** (ışık yarıçapı +%40, ve karanlıkta hasarın %10 artar)

---

# ARA SAHNE 4 — "ÜÇÜNCÜ İŞARET" (bölüm sonu, ~8 saniye)

**Panel A.** Rey mangalın yanında oturuyor. Nefes nefese. Işık yüzünde.

**Panel B.** Duvarda **Cemo'nun tırmık izi** — ama bu sefer yanında bir şey daha var: küçük bir çizim. Bir ev. Kaba, çocuk elinden.

**Panel C.** Rey kolyeyi çıkarır. Kolye **titreşiyor.** Yakınlarda.

**Panel D.** Kamera koridora döner. Aşağıda, uzakta, bir ışık daha. Ama bu sefer **turuncu** — normal ateş. Ve hareket ediyor.

**Panel E.** Birisi var aşağıda.

*Bölüm biter.*

**Kurulum:** Bu ışık B4'teki (Kayıt Odası) kampın sahibi. Ve B6'da Ardo çıkacak — oyuncu şimdiden "aşağıda biri var" biliyor. Ardo'nun girişi sürpriz değil, **beklenen bir buluşma** oluyor. Daha güçlü.

---

## DÜŞMAN DAĞILIMI

| Oda | Sürüklenen | Tırmanan | Gölge Sürüklenen | Toplam |
|---|---|---|---|---|
| 1 | 2 | — | — | 2 |
| 2 | 3 | 1 | — | 4 |
| 3 | 1 | 3 | — | 4 |
| 4 | — | — | 4 | 4 |
| 6 | 2 | 2 | 3 | 7 |
| 7 | — | — | 3 (çağrılan) | +boss |
| **Toplam** | **8** | **6** | **10** | **24 + boss** |

---

## ALTIN AKIŞI

| Kaynak | Miktar |
|---|---|
| 24 düşman × ~5 | 120 |
| Sandık (Oda 2) | 35 |
| Gizli oda ödülü (Bekçi ticareti değil, sandık) | 70 |
| Mini-boss | 70 |
| Combo bonusu | ~%25 |
| **Toplam (her şeyi bulan)** | **~370** |
| **Toplam (dikkatsiz)** | **~155** |

Mum Bekçisi'nde harcama seçeneği var — oyuncu ilk kez "biriktir mi, harca mı" kararı verir.

---

## SES TASARIMI

| An | Ses |
|---|---|
| Oda 1 | Meşale çıtırtısı **ön planda**. Ambient neredeyse yok |
| Oda 2 | Karanlıkta düşman sesleri — göremediğin şeyler duyulur. Ses haritası kullanınca **tek bir çan tınısı** |
| Ara Sahne 2 (çeteleler) | Müzik tamamen kesilir. Sadece Rey'in nefesi |
| Oda 3-A (Mum Bekçisi) | **Kendi teması** — sıcak, yavaş, hüzünlü. Tek enstrüman. Oyuncu bu melodiyi hatırlayacak, çünkü Bekçi 3 kez daha çıkacak |
| Ara Sahne 3 (Mor Alev) | Panel B'de **mutlak sessizlik** (2 sn). Sonra mor alevin sesi: alçak, sürekli, neredeyse duyulmayan bir uğultu |
| Mor alev taşınırken | Yankı fısıltıları **hiç susmaz**, hafif ama sürekli. Rahatsız edici olmalı |
| Oda 7 | Boss teması. Karanlık Dalgası anında tüm sesler kesilir, sadece kalp atışı |
| Bölüm sonu | Kolye titreşimi — ilk kez duyulur. Alçak, yumuşak, sıcak |

**Mum Bekçisi'nin teması** en önemli müzik parçası. Tekrar eden karakter = tekrar eden melodi = duygusal bağ.

---

## YENİ MEKANİKLER ÖZETİ

| Mekanik | İlk kullanım | Sonraki bölümlerde |
|---|---|---|
| Meşale taşıma/fırlatma | Oda 1 | B5 (su), B11 (ayna), B15 (sessizlik) |
| Ses haritası (sonar) | Oda 2 | B9 (çan kulesi), B15 |
| Mum Bekçisi ticareti | Oda 3-A | B7, B12, B16 |
| Mor Alev seçimi | Oda 5 | Tüm oyun (B14 twist'i etkiler) |
| Gölge düşmanlar | Oda 4 | B11, B14, B15 |
| Işıkla arena kontrolü | Oda 7 | B13 (boss 2) |

---

## BAŞARI KRİTERLERİ

- [ ] Karanlık korkutucu ama sinir bozucu değil
- [ ] Oyuncu meşaleyi bırakma kararını kendi veriyor
- [ ] Mum Bekçisi'ni gören oyuncu "bu ne?" diyor ama korkmuyor
- [ ] Mor Alev sahnesinde 2 saniyelik karanlık işe yarıyor (test: oyuncu "oyun mu dondu?" diye düşünüyor mu?)
- [ ] Mor Alev'i alan da almayan da bölümü bitirebiliyor
- [ ] Bölüm sonundaki turuncu ışık merak uyandırıyor

---

## UYGULAMA NOTLARI

**Işık sistemi bu bölümde zorlanacak.** Mevcut meşale ışığı tek kaynak; burada 5+ eşzamanlı ışık kaynağı olacak (yuvalar). Işık maskesini tek yüzeyde topla, her kaynağı `BLEND_RGBA_SUB` ile aynı yüzeye işle. Kaynak başına ayrı geçiş yapma.

**Mor alevin rengi paletten:** `echo_violet`. Bu renk sadece Yankı ve mor alevle ilişkili şeylerde kullanılır — oyuncu bilinçaltında bağlantıyı kurar.

**Mum Bekçisi'nin gözleri:** İki parçacık emitörü. Sprite'a çizme, kod ile üret — böylece titreşir, canlı görünür.

**Karanlık ≠ siyah.** Tam siyah ucuz durur. En koyu palet rengi + hafif mavi ton kullan. Ve karanlıkta bile siluetler **çok hafif** seçilsin (%8 alfa) — oyuncu tamamen kör olmasın.
